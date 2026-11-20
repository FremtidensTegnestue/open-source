//! Run the tagged SolidCraft rail through FieldCraft's linear solid solver.
use anyhow::{Context, Result, ensure};
use serde_json::{Value, json};
use std::{env, fs, path::Path, process::Command};

fn table(path: &Path, columns: &[&str], row_name: Option<&str>) -> Result<Vec<Vec<f64>>> {
    // FieldCraft's exports here contain only these fixed ASCII set names and numeric cells.
    let csv = fs::read_to_string(path)?;
    let mut lines = csv.lines();
    let header: Vec<_> = lines
        .next()
        .context("Missing FieldCraft CSV header")?
        .split(',')
        .collect();
    let indices = columns
        .iter()
        .map(|col| {
            header
                .iter()
                .position(|h| h == col)
                .with_context(|| format!("Missing column {col} in {}", path.display()))
        })
        .collect::<Result<Vec<_>>>()?;
    let mut rows = Vec::new();
    for line in lines {
        let cells: Vec<_> = line.split(',').collect();
        if row_name.is_some_and(|name| cells.first() != Some(&name)) {
            continue;
        }
        let values = indices
            .iter()
            .map(|&i| -> Result<f64> {
                let value = cells
                    .get(i)
                    .context("Short FieldCraft CSV row")?
                    .parse::<f64>()?;
                ensure!(value.is_finite(), "Non-finite FieldCraft result");
                Ok(value)
            })
            .collect::<Result<Vec<_>>>()?;
        rows.push(values);
    }
    ensure!(
        !rows.is_empty(),
        "No FieldCraft result in {}",
        path.display()
    );
    Ok(rows)
}

/// Positive force acts downwards on this single rail. Length in mm, force in N, input E in Pa.
pub fn analyse(
    geometry: &Path,
    e_pa: f64,
    nu: f64,
    end_force_n: f64,
    mesh_size_mm: f64,
) -> Result<Value> {
    ensure!(
        e_pa.is_finite() && e_pa > 0.0 && nu > -1.0 && nu < 0.5,
        "Invalid isotropic elastic constants"
    );
    ensure!(
        end_force_n.is_finite()
            && end_force_n >= 0.0
            && mesh_size_mm.is_finite()
            && mesh_size_mm > 0.0,
        "Invalid force or mesh size"
    );
    let geometry = geometry.canonicalize()?;
    let dir = tempfile::tempdir()?;
    let mut commands: Vec<Value> = serde_json::from_str(include_str!("rail.json"))?;
    for entry in &mut commands {
        match entry["command"].as_str() {
            Some("geometry.import.mesh") => entry["params"]["path"] = json!(geometry),
            Some("mesh.hex.generate") => entry["params"]["size"] = json!(mesh_size_mm),
            Some("model.material.create") => {
                entry["params"]["elastic"]["young"] = json!(e_pa / 1e6);
                entry["params"]["elastic"]["poisson"] = json!(nu);
            }
            Some("model.load.create") => {
                entry["params"]["vector"] = json!([0.0, 0.0, -end_force_n])
            }
            _ => {}
        }
    }
    fs::write(dir.path().join("run.json"), serde_json::to_vec(&commands)?)?;
    let bin = env::var_os("FIELDCRAFT_CLI").unwrap_or_else(|| "fieldcraft-cli".into());
    let output = Command::new(&bin).current_dir(dir.path()).args(["run", "run.json"]).output()
        .context("Starting fieldcraft-cli; install it on PATH or set FIELDCRAFT_CLI to its absolute path")?;
    ensure!(
        output.status.success(),
        "fieldcraft-cli run failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let info: Value =
        serde_json::from_slice(&output.stdout).context("Reading FieldCraft model.info")?;
    ensure!(
        info["display_units"] == "mm-t-s-N-MPa",
        "Unexpected FieldCraft display units: {info}"
    );
    let nodes = info["nodes"]
        .as_u64()
        .context("Missing FieldCraft node count")?;
    let elements = info["elements"]["hex20"]
        .as_u64()
        .context("Missing quadratic solid elements")?;
    ensure!(elements > 0, "Empty FieldCraft mesh");
    let all = table(
        &dir.path().join("nodes.csv"),
        &["x [mm]", "y [mm]", "z [mm]", "s_xx [MPa]"],
        None,
    )?;
    ensure!(
        nodes == all.len() as u64,
        "Body set does not cover the analysis mesh"
    );
    let mut lo = [f64::INFINITY; 3];
    let mut hi = [f64::NEG_INFINITY; 3];
    for row in &all {
        for j in 0..3 {
            lo[j] = lo[j].min(row[j]);
            hi[j] = hi[j].max(row[j]);
        }
    }
    for j in 0..3 {
        ensure!(
            lo[j].abs() < 1e-6 && (hi[j] - [300.0, 30.0, 10.0][j]).abs() < 1e-6,
            "FieldCraft rail dimension or placement differs on axis {j}"
        );
    }
    // Report the nearest actual node, including its location on the top surface.
    let probe_target = [150.0, 15.0, 10.0];
    let squared_distance = |p: &[f64]| {
        (0..3)
            .map(|j| (p[j] - probe_target[j]).powi(2))
            .sum::<f64>()
    };
    let probe = all
        .iter()
        .filter(|p| (p[2] - probe_target[2]).abs() < 1e-6)
        .min_by(|a, b| squared_distance(a).total_cmp(&squared_distance(b)))
        .context("No upper surface stress probe")?;
    let tip = table(&dir.path().join("tip.csv"), &["x [mm]", "uz [mm]"], None)?;
    let end_nodes = all.iter().filter(|r| (r[0] - 300.0).abs() < 1e-6).count();
    ensure!(
        tip.len() == end_nodes && tip.iter().all(|r| (r[0] - 300.0).abs() < 1e-6),
        "Loaded set does not match the free end"
    );
    let mean_tip = tip.iter().map(|r| r[1]).sum::<f64>() / tip.len() as f64;
    let reaction_csv = dir.path().join("reactions.csv");
    let support = table(
        &reaction_csv,
        &["nodes", "fz [N]", "my [N·mm]"],
        Some("Vaeg"),
    )?;
    let root_nodes = all.iter().filter(|r| r[0].abs() < 1e-6).count();
    ensure!(
        support.len() == 1 && support[0][0] == root_nodes as f64,
        "Unexpected support node count"
    );
    let applied = table(&reaction_csv, &["fz [N]"], Some("applied"))?;
    ensure!(
        applied.len() == 1 && (applied[0][0] + end_force_n).abs() < 1e-7 * end_force_n.max(1.0),
        "FieldCraft applied force does not match input"
    );
    Ok(json!({
        "element_type":"hex20", "mesh_size_mm":mesh_size_mm, "elements":elements, "nodes":nodes,
        "mesh_min_mm":lo, "mesh_max_mm":hi, "young_modulus_pa":e_pa, "poisson_ratio":nu,
        "applied_z_n":applied[0][0], "tip_nodes":tip.len(), "tip_z_mm":mean_tip,
        "reaction_z_n":support[0][1], "reaction_y_nm":support[0][2]/1000.0,
        "stress_probe_xyz_mm":&probe[..3], "stress_xx_mpa":probe[3]
    }))
}
