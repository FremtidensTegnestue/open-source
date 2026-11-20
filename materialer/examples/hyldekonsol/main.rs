//! Regenerate this shelf's quantities, impacts and statics from the pinned sources and models.
use anyhow::{Context, Result, ensure};
use clap::Parser;
use serde_json::{Value, json};
use std::{collections::BTreeMap, fs, path::Path, process::Command};

const EXAMPLE: &str = "examples/hyldekonsol";
const GRAVITY: f64 = 9.81;

#[derive(Parser)]
struct Args {
    /// Combined downward force at the front edge, centred between the two rails (N).
    #[arg(long, default_value_t = 100.0)]
    front_load_n: f64,
}

fn command_json(command: &mut Command) -> Result<Value> {
    let output = command
        .output()
        .with_context(|| format!("Start {command:?}"))?;
    ensure!(
        output.status.success(),
        "{command:?}: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).with_context(|| format!("Invalid JSON from {command:?}"))
}

fn number(value: &Value, key: &str) -> Result<f64> {
    value[key]
        .as_f64()
        .filter(|n| n.is_finite())
        .with_context(|| format!("Missing number: {key}"))
}

fn string<'a>(value: &'a Value, key: &str) -> Result<&'a str> {
    value[key]
        .as_str()
        .with_context(|| format!("Missing text: {key}"))
}

fn checked_inputs(root: &Path) -> Result<(String, BTreeMap<String, f64>)> {
    let selection: Value = serde_json::from_slice(&fs::read(root.join("materialevalg.json"))?)?;
    let snapshot = string(&selection, "snapshot")?;
    let mut values = BTreeMap::new();
    for (name, unit, module, reference) in [
        ("steel_density", "kg/m3", None, None),
        ("steel_young", "Pa", None, None),
        ("steel_poisson", "1", None, None),
        ("steel_yield", "Pa", None, None),
        ("steel_gwp", "kg CO2-eq", Some("A1-A3"), Some("1 ton")),
        ("board_density", "kg/m³", None, None),
        ("board_gwp", "kg CO2-eq", Some("A1-A3"), Some("1 m³")),
        ("board_c3", "kg CO2-eq", Some("C3"), Some("1 m³")),
    ] {
        let selected = &selection["inputs"][name];
        let found = command_json(Command::new("ft-materials").args([
            "--snapshot",
            snapshot,
            "lookup",
            string(selected, "material_id")?,
            "--property",
            string(selected, "property_id")?,
        ]))?;
        ensure!(
            found["snapshot"] == snapshot,
            "Unexpected edition for {name}"
        );
        let obs = found["observations"]
            .as_array()
            .context("Missing observations")?
            .iter()
            .find(|o| o["id"] == selected["observation_id"])
            .with_context(|| format!("Missing observation {name}"))?;
        for key in [
            "source_id",
            "source_version_id",
            "source_locator",
            "source_url",
            "unit",
            "value",
            "material_id",
            "property_id",
        ] {
            ensure!(
                obs[key] == selected[key],
                "Source mismatch for {name}/{key}"
            );
        }
        // A technical observation may carry its source's reference basis (e.g. BR18 density).
        ensure!(obs["unit"] == unit, "Unexpected unit for {name}");
        if let Some(module) = module {
            ensure!(
                obs["module"] == module && obs["declared_unit"].as_str() == reference,
                "Unexpected climate module or reference quantity for {name}"
            );
        }
        values.insert(name.to_string(), number(obs, "value")?);
    }
    Ok((snapshot.to_owned(), values))
}

fn geometry(root: &Path) -> Result<(Value, Value, Value)> {
    let cad = command_json(
        Command::new("ft-materials")
            .arg("extract")
            .arg(root.join("cad/model.sc"))
            .args(["--software", "solidcraft"]),
    )?;
    let bim = command_json(
        Command::new("ft-materials")
            .arg("extract")
            .arg(root.join("cad/model.bimc"))
            .args(["--software", "bimcraft", "--mesh-quantities"]),
    )?;
    let cad_parts = cad["elements"].as_array().context("Missing CAD elements")?;
    let bim_parts = bim["elements"].as_array().context("Missing BIM elements")?;
    ensure!(
        cad_parts.len() == 3 && bim_parts.len() == 3,
        "Expected three model elements"
    );
    let mut parts = serde_json::Map::new();
    for (name, label) in [
        ("Rail_A", "S235"),
        ("Rail_B", "S235"),
        ("Shelf", "Krydsfiner, ubehandlet"),
    ] {
        let a = cad_parts
            .iter()
            .find(|p| p["source_ref"]["body_name"] == name)
            .context("Missing CAD body")?;
        let b = bim_parts
            .iter()
            .find(|p| p["source_ref"]["family_name"] == name)
            .context("Missing BIM family")?;
        ensure!(
            a["material_name"] == label && b["material_name"] == label,
            "Material binding differs for {name}"
        );
        let volume = number(a, "volume_m3")?;
        let bim_volume = number(b, "volume_m3")?;
        let dims = &a["dimensions_m"];
        ensure!(
            volume > 0.0
                && (bim_volume - volume).abs() < 1e-10
                && (number(dims, "x")? * number(dims, "y")? * number(dims, "z")? - volume).abs()
                    < 1e-10,
            "Solid and BIM measurements disagree or {name} is not a full rectangular prism"
        );
        parts.insert(name.to_string(), json!({"dimensions_m":dims,"cad_volume_m3":volume,"bim_volume_m3":bim_volume,"bim_guid":b["source_ref"]["guid"],"model_material":label}));
    }
    ensure!(
        parts["Rail_A"]["dimensions_m"] == parts["Rail_B"]["dimensions_m"],
        "Expected a symmetric pair of rails"
    );
    Ok((
        Value::Object(parts),
        cad["software_version"].clone(),
        bim["software_version"].clone(),
    ))
}

fn section_result(
    length: f64,
    width: f64,
    height: f64,
    young: f64,
    tip_force: f64,
    distributed: f64,
) -> Value {
    // SI. distributed is a uniform downward load on one rail in N/m.
    let inertia = width * height.powi(3) / 12.0;
    let moment = tip_force * length + distributed * length.powi(2) / 2.0;
    let reaction = tip_force + distributed * length;
    let deflection = tip_force * length.powi(3) / (3.0 * young * inertia)
        + distributed * length.powi(4) / (8.0 * young * inertia);
    json!({"tip_force_down_n":tip_force,"distributed_load_n_m":distributed,
           "second_moment_m4":inertia,"wall_reaction_up_n":reaction,"wall_moment_magnitude_nm":moment,
           "nominal_outer_fibre_stress_mpa":moment*height/(2.0*inertia)/1e6,
           "max_rectangular_shear_mpa":1.5*reaction/(width*height)/1e6,
           "tip_z_mm":-1000.0*deflection})
}

fn main() -> Result<()> {
    let args = Args::parse();
    ensure!(
        args.front_load_n.is_finite() && args.front_load_n > 0.0,
        "Use a positive, finite front load in N"
    );
    let root = Path::new(EXAMPLE);
    let (snapshot, inputs) = checked_inputs(root)?;
    let (mut parts, cad_version, bim_version) = geometry(root)?;
    let mut total_mass = 0.0;
    let mut total_gwp = 0.0;
    for (name, part) in parts.as_object_mut().context("Missing parts")? {
        let volume = number(part, "cad_volume_m3")?;
        let (mass, gwp) = if name == "Shelf" {
            (
                volume * inputs["board_density"],
                volume * inputs["board_gwp"],
            )
        } else {
            let mass = volume * inputs["steel_density"];
            (mass, mass / 1000.0 * inputs["steel_gwp"])
        };
        part["mass_kg"] = json!(mass);
        part["gwp_a1_a3_kg_co2e"] = json!(gwp);
        total_mass += mass;
        total_gwp += gwp;
    }
    let dims = &parts["Rail_A"]["dimensions_m"];
    let length = number(dims, "x")?;
    let width = number(dims, "y")?;
    let height = number(dims, "z")?;
    let force = args.front_load_n / 2.0;
    let young = inputs["steel_young"];
    let self_weight = total_mass * GRAVITY;
    let mut point = section_result(length, width, height, young, force, 0.0);
    let mut combined = section_result(
        length,
        width,
        height,
        young,
        force,
        self_weight / (2.0 * length),
    );
    let yield_mpa = inputs["steel_yield"] / 1e6;
    for case in [&mut point, &mut combined] {
        let ratio = number(case, "nominal_outer_fibre_stress_mpa")? / yield_mpa;
        case["nominal_stress_over_reference_yield"] = json!(ratio);
        case["nominal_stress_reaches_reference_yield"] = json!(ratio >= 1.0);
        case["tip_displacement_over_span"] =
            json!(number(case, "tip_z_mm")?.abs() / (length * 1000.0));
    }
    let solver = run_fieldcraft(root, young, inputs["steel_poisson"], force, &point)?;
    let field_cli = std::env::var_os("FIELDCRAFT_CLI").unwrap_or_else(|| "fieldcraft-cli".into());
    let solver_version = Command::new(field_cli).arg("--version").output()?;
    ensure!(
        solver_version.status.success(),
        "Could not read FieldCraft version"
    );
    let report = json!({
        "snapshot":snapshot,"software":{"solidcraft":cad_version,"bimcraft":bim_version,"fieldcraft":std::str::from_utf8(&solver_version.stdout)?.trim()},
        "parts":parts,"totals":{"mass_kg":total_mass,"self_weight_n":self_weight,
         "gwp_a1_a3_kg_co2e":total_gwp,"board_only_c3_kg_co2e":number(&parts["Shelf"],"cad_volume_m3")?*inputs["board_c3"]},
        "front_load_total_n":args.front_load_n,"per_rail_analytical":{"front_load_only":point, "front_load_plus_uniform_self_weight":combined},
        "fieldcraft_front_load_only":solver,"steel_reference_yield_mpa":yield_mpa,
    });
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

#[path = "fieldcraft/run.rs"]
mod fieldcraft;

fn run_fieldcraft(
    root: &Path,
    young_pa: f64,
    poisson: f64,
    force: f64,
    analytical: &Value,
) -> Result<Value> {
    let rail = root.join("cad/rail.3mf");
    let coarse = fieldcraft::analyse(&rail, young_pa, poisson, force, 10.0)?;
    let fine = fieldcraft::analyse(&rail, young_pa, poisson, force, 5.0)?;
    let expected = number(analytical, "tip_z_mm")?;
    let fine_tip = number(&fine, "tip_z_mm")?;
    let mesh_change = (number(&coarse, "tip_z_mm")? - fine_tip).abs() / fine_tip.abs();
    let beam_difference = (fine_tip - expected).abs() / expected.abs();
    // Acceptance criteria for this slender rectangular benchmark, not for designing a building.
    ensure!(
        mesh_change < 0.01 && beam_difference < 0.03,
        "Unexpected tip displacement: check mesh, units and loading"
    );
    for mesh in [&coarse, &fine] {
        let reaction = number(mesh, "reaction_z_n")?;
        let moment = number(mesh, "reaction_y_nm")?;
        let expected_moment = number(analytical, "wall_moment_magnitude_nm")?;
        ensure!(
            (reaction - force).abs() < force * 1e-5
                && (moment + expected_moment).abs() < expected_moment * 1e-5,
            "Forces or moments do not balance for this model"
        );
    }
    let midspan_stress = number(analytical, "nominal_outer_fibre_stress_mpa")? / 2.0;
    for mesh in [&coarse, &fine] {
        let xyz = mesh["stress_probe_xyz_mm"]
            .as_array()
            .context("Missing stress probe position")?;
        ensure!(
            xyz.len() == 3
                && xyz
                    .iter()
                    .zip([150.0, 15.0, 10.0])
                    .all(|(v, target)| v.as_f64().is_some_and(|n| (n - target).abs() < 1e-6)),
            "Stress probe and analytical section are at different positions"
        );
        ensure!(
            (number(mesh, "stress_xx_mpa")? - midspan_stress).abs() < 0.03 * midspan_stress,
            "Midspan upper-fibre tensile stress differs from beam theory"
        );
    }
    Ok(
        json!({"coarse":coarse,"fine":fine,"midspan_upper_fibre_beam_stress_mpa":midspan_stress,
        "mesh_tip_change_percent":mesh_change*100.0,"fine_vs_beam_tip_difference_percent":beam_difference*100.0}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn centred_front_load_and_uniform_self_weight() {
        let point = section_result(0.3, 0.03, 0.01, 210e9, 50.0, 0.0);
        let combined = section_result(0.3, 0.03, 0.01, 210e9, 50.0, 11.168685 / 0.3);
        let value = |row: &Value, key: &str| row[key].as_f64().unwrap();
        assert!((value(&point, "tip_z_mm") + 6.0 / 7.0).abs() < 1e-10);
        assert!((value(&point, "nominal_outer_fibre_stress_mpa") - 30.0).abs() < 1e-10);
        assert!((value(&combined, "wall_reaction_up_n") - 61.168685).abs() < 1e-8);
        assert!((value(&combined, "wall_moment_magnitude_nm") - 16.67530275).abs() < 1e-8);
        assert!((value(&combined, "tip_z_mm") + 0.92894).abs() < 0.0001);
    }
}
