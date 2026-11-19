//! Volumes for closed, connected, consistently oriented imported triangle shells.
use anyhow::{Context, Result, ensure};
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};

const TOL: f64 = 1e-5;
const PLANE: &str = "9e3c0a10-1f0b-4d8c-8a5e-0000000000a1";
type Point = [f64; 3];

fn minus(a: Point, b: Point) -> Point {
    [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
}
fn dot(a: Point, b: Point) -> f64 {
    a.iter().zip(b).map(|(a, b)| a * b).sum()
}
fn cross(a: Point, b: Point) -> Point {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}

fn weld(
    p: Point,
    vertices: &mut Vec<Point>,
    buckets: &mut HashMap<[i64; 3], Vec<usize>>,
) -> Result<usize> {
    ensure!(
        p.iter().all(|n| n.is_finite() && (n / TOL).abs() < 1e18),
        "Coordinate outside welding range"
    );
    let key = p.map(|n| (n / TOL).floor() as i64);
    for x in -1..=1 {
        for y in -1..=1 {
            for z in -1..=1 {
                if let Some(ids) = buckets.get(&[key[0] + x, key[1] + y, key[2] + z]) {
                    for &idx in ids {
                        let d = minus(p, vertices[idx]);
                        if dot(d, d) <= TOL * TOL {
                            return Ok(idx);
                        }
                    }
                }
            }
        }
    }
    let i = vertices.len();
    vertices.push(p);
    buckets.entry(key).or_default().push(i);
    Ok(i)
}

fn reachable(start: usize, adj: &[Vec<usize>], allowed: Option<&HashSet<usize>>) -> usize {
    let mut pending = vec![start];
    let mut seen = HashSet::from([start]);
    while let Some(i) = pending.pop() {
        for &j in &adj[i] {
            if allowed.is_none_or(|s| s.contains(&j)) && seen.insert(j) {
                pending.push(j)
            }
        }
    }
    seen.len()
}

pub(super) fn volume(mesh: &Value) -> Result<f64> {
    let triangles = mesh
        .as_array()
        .filter(|v| !v.is_empty())
        .context("Empty or missing triangle mesh")?;
    let mut vertices = Vec::new();
    let mut buckets = HashMap::new();
    let mut faces = Vec::new();
    let mut unique_faces = HashSet::new();
    let mut edges: HashMap<[usize; 2], Vec<(usize, usize, usize)>> = HashMap::new();
    let mut incident: HashMap<usize, HashSet<usize>> = HashMap::new();
    for (idx, t) in triangles.iter().enumerate() {
        let points = t
            .as_array()
            .filter(|p| p.len() == 3)
            .context("Faces must have three vertices")?;
        let mut face = [0; 3];
        for (i, p) in points.iter().enumerate() {
            let point: Point =
                serde_json::from_value(p.clone()).context("Expected 3D point in mm")?;
            face[i] = weld(point, &mut vertices, &mut buckets)?;
        }
        let mut face_key = face;
        face_key.sort_unstable();
        ensure!(
            unique_faces.insert(face_key),
            "Coincident duplicate triangle"
        );
        let [a, b, c] = face.map(|i| vertices[i]);
        let n = cross(minus(b, a), minus(c, a));
        let area2 = dot(n, n);
        ensure!(
            area2.is_finite() && area2 > TOL.powi(4),
            "Degenerate triangle"
        );
        for i in 0..3 {
            let a = face[i];
            let b = face[(i + 1) % 3];
            let edge = [a.min(b), a.max(b)];
            edges.entry(edge).or_default().push((idx, a, b));
            incident.entry(a).or_default().insert(idx);
        }
        faces.push(face);
    }
    let mut adj = vec![Vec::new(); faces.len()];
    for uses in edges.values() {
        ensure!(uses.len() == 2, "Open or nonmanifold edge");
        let (a, x, y) = uses[0];
        let (b, z, w) = uses[1];
        ensure!(x == w && y == z, "Inconsistent triangle winding");
        adj[a].push(b);
        adj[b].push(a);
    }
    ensure!(
        reachable(0, &adj, None) == faces.len(),
        "Disconnected shells"
    );
    for fan in incident.values() {
        ensure!(
            reachable(*fan.iter().next().unwrap(), &adj, Some(fan)) == fan.len(),
            "Nonmanifold vertex"
        );
    }
    let mut sum = 0.0_f64;
    let mut correction = 0.0;
    for face in faces {
        let [a, b, c] = face.map(|i| minus(vertices[i], vertices[0]).map(|n| n / 1000.0));
        let term = dot(a, cross(b, c)) / 6.;
        let t = sum + term;
        correction += if sum.abs() >= term.abs() {
            (sum - t) + term
        } else {
            (term - t) + sum
        };
        sum = t;
    }
    let result = (sum + correction).abs();
    ensure!(
        result.is_finite() && result > 0.0,
        "No positive enclosed volume"
    );
    Ok(result)
}

fn known(row: &Value, names: &str) -> bool {
    row.as_object()
        .is_some_and(|obj| obj.keys().all(|k| names.split_whitespace().any(|n| n == k)))
}
fn empty_values(row: &Value) -> bool {
    row.as_object()
        .is_some_and(|obj| obj.values().all(|v| *v == json!({})))
}
fn finite(v: &Value) -> bool {
    v.as_f64().is_some_and(f64::is_finite)
}

pub(super) fn family(row: &Value, reply: &Value) -> Result<(f64, Option<String>, Value)> {
    let family = &reply["family"];
    let forms = &family["forms"];
    let opts = &reply["options"];
    ensure!(
        reply["name"] == row["family"] && row["category"] == "component",
        "Wrong family or element category"
    );
    ensure!(
        reply["warnings"].is_null() || reply["warnings"] == json!([]),
        "Family warnings require review"
    );
    ensure!(
        known(family, "category parameters types forms planes")
            && family["category"] == "generic"
            && family["parameters"] == json!([]),
        "Unsupported family context or parameters"
    );
    let typ = row["type"].as_str().context("Missing family type")?;
    ensure!(
        family["types"][typ] == json!({})
            && empty_values(&family["types"])
            && (reply["values"].is_null() || empty_values(&reply["values"]))
            && (row["values"].is_null() || row["values"] == json!({})),
        "Unsupported family/instance values"
    );
    ensure!(
        known(
            row,
            "id guid name mark category family family_guid type values angle at level offset offset_from_host shared_east shared_north shared_elevation height work_plane material area_m2 volume_m3 mirrored"
        ),
        "Unknown component placement or scaling"
    );
    for k in [
        "angle",
        "offset",
        "offset_from_host",
        "shared_east",
        "shared_north",
        "shared_elevation",
        "height",
    ] {
        ensure!(
            row.get(k).is_none() || finite(&row[k]),
            "Nonfinite instance placement"
        );
    }
    ensure!(
        row.get("at").is_none()
            || row["at"]
                .as_array()
                .is_some_and(|a| a.len() == 2 && a.iter().all(finite)),
        "Invalid component position"
    );
    ensure!(
        row.get("mirrored").is_none() || row["mirrored"].is_boolean(),
        "Invalid mirror flag"
    );
    ensure!(
        opts.is_null()
            || (known(
                opts,
                "always_vertical cut_in_views cut_with_voids_when_loaded default_elevation omniclass room_calculation_point shared work_plane_based"
            ) && opts
                .get("cut_with_voids_when_loaded")
                .is_none_or(|v| *v == false)
                && opts.get("work_plane_based").is_none_or(|v| *v == false)),
        "Unsupported family options"
    );
    let forms = forms
        .as_array()
        .filter(|f| f.len() == 1)
        .context("Expected one solid mesh form")?;
    let f = &forms[0];
    let guid = f["guid"]
        .as_str()
        .filter(|s| !s.is_empty())
        .context("Missing form GUID")?;
    ensure!(
        known(f, "id guid host from to material mesh visible void")
            && f.get("visible").is_none_or(|v| *v == true)
            && f.get("void").is_none_or(|v| *v == false),
        "Unsupported or hidden form"
    );
    ensure!(
        f["host"] == json!({"plane":PLANE})
            && f["from"].as_f64() == Some(0.0)
            && f["to"].as_f64() == Some(0.0),
        "Unexpected form reference plane"
    );
    let p = family["planes"]
        .as_array()
        .and_then(|ps| ps.iter().find(|p| p["guid"] == PLANE))
        .context("Missing reference plane")?;
    fn coord(v: &Value, expected: Point) -> bool {
        serde_json::from_value::<Point>(v.clone()).is_ok_and(|p| p == expected)
    }
    ensure!(
        coord(&p["start"], [-1000., 0., 0.])
            && coord(&p["end"], [1000., 0., 0.])
            && coord(&p["up"], [0., 1000., 0.])
            && p["defines_origin"] == true
            && p["level"] == true,
        "Modified reference plane"
    );
    let v = volume(&f["mesh"])?;
    Ok((
        v,
        f["material"]
            .as_str()
            .filter(|s| !s.trim().is_empty())
            .map(str::to_owned),
        json!({
        "quantity_api":"bimcraft-cli family mesh","source_form_guid":guid,"source_form_id":f["id"],"triangle_count":f["mesh"].as_array().unwrap().len(),
        "volume_method":"closed oriented triangle shell, compensated tetrahedron sum in m3","vertex_welding_tolerance_mm":TOL,
        "mesh_quantity_limits":"Single rigid imported shell; self-intersections and curved-surface tessellation error are not checked",
        "self_intersection_checked":false}),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_open_reversed_and_disconnected_meshes() {
        let a = json!([0, 0, 0]);
        let b = json!([1000, 0, 0]);
        let c = json!([0, 1000, 0]);
        let d = json!([0, 0, 1000]);
        let mut t = json!([[a, c, b], [a, b, d], [a, d, c], [b, c, d]]);
        assert!((volume(&t).unwrap() - 1. / 6.).abs() < 1e-12);
        let mut removed = t.clone();
        removed.as_array_mut().unwrap().pop();
        assert!(volume(&removed).is_err());
        let mut reversed = t.clone();
        reversed[0].as_array_mut().unwrap().reverse();
        assert!(volume(&reversed).is_err());
        let mut extra = t.clone();
        for f in extra.as_array_mut().unwrap() {
            for p in f.as_array_mut().unwrap() {
                p[0] = json!(p[0].as_i64().unwrap() + 4000);
            }
        }
        t.as_array_mut()
            .unwrap()
            .extend(extra.as_array().unwrap().clone());
        assert!(volume(&t).is_err());
    }
}
