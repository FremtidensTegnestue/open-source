use super::{Software, mesh};
use anyhow::{Context, Result, bail, ensure};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeSet, HashMap, HashSet},
    fs::File,
    io::{Read, Seek},
    path::Path,
    process::{Command, Stdio},
    time::{Duration, Instant},
};

pub(super) fn hash(path: &Path) -> Result<String> {
    let mut h = Sha256::new();
    std::io::copy(&mut File::open(path)?, &mut h)?;
    Ok(hex::encode(h.finalize()))
}
fn command(binary: &str, args: &[String]) -> Result<String> {
    let mut out = tempfile::tempfile()?;
    let mut err = tempfile::tempfile()?;
    let mut child = Command::new(binary)
        .args(args)
        .stdin(Stdio::null())
        .stdout(out.try_clone()?)
        .stderr(err.try_clone()?)
        .spawn()
        .with_context(|| format!("Could not run {binary}"))?;
    let start = Instant::now();
    loop {
        if let Some(status) = child.try_wait()? {
            if !status.success() {
                err.rewind()?;
                let mut msg = String::new();
                err.take(8192).read_to_string(&mut msg)?;
                bail!("{binary}: {status} {msg}");
            }
            break;
        }
        if start.elapsed() > Duration::from_secs(120) {
            let _ = child.kill();
            let _ = child.wait();
            bail!("{binary} timed out")
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    out.rewind()?;
    let mut s = String::new();
    out.read_to_string(&mut s)?;
    Ok(s)
}
fn finite(v: &Value) -> Option<f64> {
    v.as_f64().filter(|n| n.is_finite() && *n >= 0.)
}
fn solid(path: &str) -> Result<(Vec<Value>, Vec<Value>)> {
    let doc: Value =
        serde_json::from_str(&command("solidcraft-cli", &["eval".into(), path.into()])?)?;
    ensure!(
        !doc["timeline"].as_array().is_some_and(|steps| steps
            .iter()
            .any(|s| s["error"].as_str().is_some_and(|e| !e.is_empty()))),
        "SolidCraft reports a failed feature"
    );
    let mut rows = Vec::new();
    let mut warnings = Vec::new();
    let mut seen = HashSet::new();
    for (i, b) in doc["bodies"]
        .as_array()
        .context("Missing SolidCraft bodies")?
        .iter()
        .enumerate()
    {
        let name = b["name"]
            .as_str()
            .filter(|s| !s.is_empty())
            .context("Unnamed body")?;
        ensure!(seen.insert(name), "Duplicate body name: {name}");
        let id = format!("solidcraft:{name}");
        let material = b["material"]
            .as_str()
            .filter(|m| !m.trim().is_empty() && !m.eq_ignore_ascii_case("Default"));
        let volume = if b["closed"] == true {
            finite(&b["volume_mm3"]).map(|v| v / 1e9)
        } else {
            None
        };
        if volume.is_none() {
            warnings.push(json!({"code":"volume_unavailable","element_id":id}));
        }
        if material.is_none() {
            warnings.push(json!({"code":"material_unspecified","element_id":id}));
        }
        let lower = serde_json::from_value::<[f64; 3]>(b["bbox"]["min"].clone()).ok();
        let upper = serde_json::from_value::<[f64; 3]>(b["bbox"]["max"].clone()).ok();
        let bounds = lower.zip(upper).and_then(|(lo, hi)| {
            let d = [
                (hi[0] - lo[0]) / 1000.,
                (hi[1] - lo[1]) / 1000.,
                (hi[2] - lo[2]) / 1000.,
            ];
            d.iter()
                .all(|n| n.is_finite() && *n >= 0.)
                .then(|| json!({"x":d[0],"y":d[1],"z":d[2]}))
        });
        rows.push(json!({"id":id,"name":name,"volume_m3":volume,"area_m2":null,"surface_area_m2":finite(&b["area_mm2"]).map(|v|v/1e6),
            "material_name":material,"dimensions_m":bounds,"source_ref":{"body_index":i,"body_name":name,"closed":b["closed"],"measured_by":b["measured_by"],
            "quantity_api":"solidcraft-cli eval","volume_field":format!("/bodies/{i}/volume_mm3"),"volume_unit_conversion":"mm3 / 1000000000 = m3"}}));
    }
    Ok((rows, warnings))
}
fn bim_run(path: &str, verbs: &[(String, Value)]) -> Result<Vec<Value>> {
    let mut args = vec!["run".to_owned(), path.to_owned()];
    for (verb, params) in verbs {
        args.push("--cmd".into());
        args.push(format!("{verb} {params}"));
    }
    let stdout = command("bimcraft-cli", &args)?;
    stdout
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let v: Value = serde_json::from_str(l)?;
            ensure!(
                v["error"].is_null() && v["ok"] != false,
                "BIMCraft failed: {v}"
            );
            Ok(v)
        })
        .collect()
}
fn page(replies: &[Value]) -> Result<(&Vec<Value>, usize)> {
    let p = replies
        .iter()
        .find(|v| v["elements"].is_array() && v.get("returned").is_some())
        .context("Missing element page")?;
    let rows = p["elements"].as_array().unwrap();
    let count = p["count"].as_u64().context("Missing element count")? as usize;
    ensure!(
        p["returned"].as_u64() == Some(rows.len() as u64) && rows.len() <= count,
        "Invalid BIMCraft element page"
    );
    Ok((rows, count))
}
fn is_material_element(row: &Value) -> bool {
    !matches!(
        row["category"].as_str(),
        Some(
            "level"
                | "grid"
                | "view"
                | "sheet"
                | "schedule"
                | "text"
                | "dimension"
                | "tag"
                | "section"
                | "elevation"
                | "detail_line"
                | "model_line"
                | "reference_plane"
                | "property_line"
                | "camera"
                | "image"
                | "point_cloud"
        )
    )
}
fn direct_material<'a>(r: &'a Value, typ: &'a Value) -> Option<&'a str> {
    if let Some(layers) = typ["layers"].as_array().filter(|ls| !ls.is_empty()) {
        let mut mats = BTreeSet::new();
        for layer in layers
            .iter()
            .filter(|l| finite(&l["thickness"]).is_some_and(|t| t > 0.0))
        {
            mats.insert(
                layer["material"]
                    .as_str()
                    .filter(|m| !m.trim().is_empty())?,
            );
        }
        if mats.len() == 1 {
            return mats.into_iter().next();
        }
        return None;
    }
    r["material"]
        .as_str()
        .or_else(|| typ["material"].as_str())
        .filter(|m| !m.trim().is_empty())
}
fn bim(path: &str, measure_mesh: bool) -> Result<(Vec<Value>, Vec<Value>)> {
    let first = bim_run(
        path,
        &[
            ("inspect".into(), json!({})),
            ("elements".into(), json!({"offset":0,"limit":1000})),
        ],
    )?;
    let inspect = first
        .iter()
        .find(|r| r["types"].is_object())
        .context("Missing BIMCraft inspect data")?;
    let mut warnings = Vec::new();
    for warning in inspect["warnings"].as_array().into_iter().flatten() {
        warnings.push(json!({"code":"bimcraft_model_warning","message":warning}));
    }
    if let Some(imp) = first
        .iter()
        .find(|v| v.get("skipped").is_some() && v.get("format").is_some())
        && (imp["skipped"].as_array().is_some_and(|s| !s.is_empty())
            || imp["generic"].as_u64().unwrap_or(0) > 0)
    {
        warnings.push(json!({"code":"ifc_import_incomplete","source":imp}));
    }
    let (items, count) = page(&first)?;
    let mut all = items.clone();
    while all.len() < count {
        let more = bim_run(
            path,
            &[("elements".into(), json!({"offset":all.len(),"limit":1000}))],
        )?;
        let (items, n) = page(&more)?;
        ensure!(
            n == count && !items.is_empty() && all.len() + items.len() <= count,
            "Incomplete element pagination"
        );
        all.extend_from_slice(items);
    }
    let mut seen = HashSet::new();
    for r in &all {
        ensure!(
            r["id"].is_number() && seen.insert(r["id"].to_string()),
            "Invalid or duplicate BIMCraft element ID"
        );
    }
    let mut families = HashMap::new();
    if measure_mesh {
        let names: BTreeSet<_> = all
            .iter()
            .filter(|r| r["category"] == "component" && finite(&r["volume_m3"]).is_none())
            .filter_map(|r| r["family"].as_str())
            .collect();
        for chunk in names.into_iter().collect::<Vec<_>>().chunks(50) {
            let requests = chunk
                .iter()
                .map(|name| ("family".into(), json!({"name":name})))
                .collect::<Vec<_>>();
            for r in bim_run(path, &requests)? {
                if r["family"].is_object() {
                    families.insert(
                        r["name"].as_str().context("Unnamed BIM family")?.to_owned(),
                        r,
                    );
                }
            }
        }
    }
    let mut elements = Vec::new();
    for r in all.iter().filter(|r| is_material_element(r)) {
        let id = r["id"].to_string();
        let cat = r["category"].as_str().unwrap_or("");
        let typ = r["type"].as_str().unwrap_or("");
        let types = &inspect["types"];
        let type_record = &types[cat][typ];
        let type_record = if type_record.is_null() {
            &types["runs"][cat][typ]
        } else {
            type_record
        };
        let mut volume = finite(&r["volume_m3"]);
        let mut material = direct_material(r, type_record).map(str::to_owned);
        let mut source = json!({"guid":r["guid"],"family_name":r["family"],"element_id":r["id"],"quantity_api":"bimcraft-cli elements","volume_field":"volume_m3"});
        if cat == "component" && volume.is_none() && measure_mesh {
            let result = r["family"]
                .as_str()
                .and_then(|n| families.get(n))
                .context("Missing mesh family")
                .and_then(|family| mesh::family(r, family));
            match result{
                Ok((v,m,info))=>{volume=Some(v);material=m;source.as_object_mut().unwrap().extend(info.as_object().unwrap().clone());
                    warnings.push(json!({"code":"mesh_quantity_limits","severity":"notice","element_id":id}));}
                Err(e)=>warnings.push(json!({"code":"unsupported_mesh_quantity","element_id":id,"message":e.to_string()}))
            }
        }
        if material.is_none() {
            warnings.push(json!({"code":"missing_material","element_id":id}));
        }
        if volume.is_none() {
            warnings.push(json!({"code":"missing_volume","element_id":id}));
        }
        if cat == "floor" && volume.is_some() {
            source["volume_rounding_increment_m3"] = json!(0.001);
        }
        let mut d = json!({});
        for key in ["length", "height", "width", "thickness"] {
            if let Some(n) = finite(&r[key]) {
                d[key] = json!(n / 1000.);
            }
        }
        elements.push(json!({"id":id,"name":r.get("name").or_else(||r.get("type")),"material_name":material,"volume_m3":volume,
            "area_m2":finite(&r["area_m2"]),"dimensions_m":d,"category":cat,"source_ref":source}));
    }
    Ok((elements, warnings))
}

pub fn extract(path: &Path, software: Software, mesh_quantities: bool) -> Result<Value> {
    let path = path.canonicalize()?;
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();
    let program = match software {
        Software::Solidcraft => {
            ensure!(
                !mesh_quantities && matches!(ext.as_str(), "sc" | "step" | "stp"),
                "Expected a SolidCraft native model or STEP; --mesh-quantities applies to BIMCraft"
            );
            "solidcraft-cli"
        }
        Software::Bimcraft => {
            ensure!(
                matches!(ext.as_str(), "bimc" | "bimcraft" | "ifc"),
                "Expected .bimc, .bimcraft or .ifc"
            );
            "bimcraft-cli"
        }
    };
    let sha = hash(&path)?;
    let version = command(program, &["--version".into()])?;
    let version = version.trim();
    let path_str = path.to_str().context("Non-UTF8 model path")?;
    let (elements, mut warnings) = match software {
        Software::Solidcraft => solid(path_str)?,
        Software::Bimcraft => {
            ensure!(
                version == "bimcraft-cli 0.12.0",
                "Unsupported BIMCraft adapter version: {version}"
            );
            bim(path_str, mesh_quantities)?
        }
    };
    if ext == "ifc" {
        warnings.push(json!({"code":"ifc_import_context","message":"Quantities represent BIMCraft's interpretation of IFC"}));
    }
    ensure!(hash(&path)? == sha, "Model changed during inspection");
    Ok(
        json!({"schema_version":1,"software":software,"software_version":version,"model":{"path":path,"sha256":sha},
        "extraction":{"source_unchanged":true,"mesh_quantities":mesh_quantities},"elements":elements,"warnings":warnings}),
    )
}
