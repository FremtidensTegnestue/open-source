//! Reproduce the field lookup in the two shipped native models, plus a rejected binding.
use anyhow::{Context, Result, ensure};
use clap::Parser;
use serde_json::{Value, json};
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

#[derive(Parser)]
struct Args {
    #[arg(long, default_value = ".")]
    root: PathBuf,
    #[arg(long)]
    binary: Option<PathBuf>,
    #[arg(long)]
    snapshot: Option<String>,
    #[arg(long)]
    store: Option<PathBuf>,
}
fn read(path: &Path) -> Result<Value> {
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}
struct Demo {
    root: PathBuf,
    binary: PathBuf,
    store: PathBuf,
    example: PathBuf,
}
impl Demo {
    fn lookup(
        &self,
        software: &str,
        field: &str,
        selection: &Path,
        transfer: &Path,
        exit: i32,
    ) -> Result<Value> {
        let bim = software == "bimcraft";
        let model = self.example.join(if bim {
            "revised/model.bimc"
        } else {
            "revised/model.sc"
        });
        let mut cmd = Command::new(&self.binary);
        cmd.current_dir(&self.root)
            .arg("--root")
            .arg(&self.root)
            .arg("--store")
            .arg(&self.store)
            .arg("model-facts")
            .arg(model)
            .args(["--software", software, "--field", field])
            .arg("--selection")
            .arg(selection)
            .arg("--transfer")
            .arg(transfer);
        if bim {
            cmd.arg("--mesh-quantities");
        }
        let out = cmd.output()?;
        ensure!(
            out.status.code() == Some(exit),
            "{software} {field}: {} {}",
            String::from_utf8_lossy(&out.stderr),
            String::from_utf8_lossy(&out.stdout)
        );
        Ok(serde_json::from_slice(&out.stdout)?)
    }
}
fn main() -> Result<()> {
    let a = Args::parse();
    let root = a.root.canonicalize()?;
    let example = root.join("examples/unified-workflow");
    let store = a.store.unwrap_or_else(|| root.join("data/editions"));
    let exe = std::env::current_exe()?;
    let binary = a.binary.unwrap_or_else(|| {
        exe.parent()
            .unwrap()
            .parent()
            .unwrap()
            .join(format!("ft-materials{}", std::env::consts::EXE_SUFFIX))
    });
    let demo = Demo {
        root: root.clone(),
        example: example.clone(),
        binary,
        store,
    };
    let mut selection = read(&example.join("selection.json"))?;
    let snapshot = if let Some(id) = a.snapshot {
        id
    } else {
        read(&root.join("data/releases/unified-v0.3.0.json"))?["editions"]["public"]["snapshot"]
            .as_str()
            .context("Missing release edition")?
            .to_owned()
    };
    selection["snapshot"] = snapshot.clone().into();
    let temp = tempfile::tempdir()?;
    let full = temp.path().join("full.json");
    fs::write(&full, serde_json::to_vec(&selection)?)?;
    let choice = selection["materials"]["lincrete"]
        .as_object_mut()
        .context("Missing choice")?;
    for k in [
        "operations",
        "density_observation_id",
        "gwp_observation_ids",
    ] {
        choice.remove(k);
    }
    let facts_only = temp.path().join("field-selection.json");
    fs::write(&facts_only, serde_json::to_vec(&selection)?)?;
    let transfer = example.join("revised/transfer.json");
    let mut broken = read(&transfer)?;
    broken["cad_model_sha256"] = json!("changed");
    broken["bim_model_sha256"] = json!("changed");
    let stale = temp.path().join("stale.json");
    fs::write(&stale, serde_json::to_vec(&broken)?)?;
    let mut summary = json!({"status":"passed","snapshot":snapshot,"material_id":selection["materials"]["lincrete"]["material_id"]});
    let mut earlier = None;
    for soft in ["solidcraft", "bimcraft"] {
        let from_model = demo.lookup(soft, "service_life_value", &facts_only, &transfer, 0)?;
        let elem = &from_model["elements"][0];
        ensure!(
            elem["status"] == "ok" && elem["material_id"] == summary["material_id"],
            "Material not bound"
        );
        let records = elem["material_facts"]["records"]
            .as_array()
            .context("Missing field records")?;
        ensure!(
            records.len() == 2
                && [true, false]
                    .into_iter()
                    .all(
                        |inclusive| records.iter().any(|v| v["value"]["lower_bound"] == 50
                            && v["value"]["lower_inclusive"] == inclusive
                            && v["source_locator"].is_string()
                            && v["source_version_id"].is_string())
                    ),
            "The two service-life statements or their sources are missing"
        );
        if let Some(first) = &earlier {
            ensure!(
                first == &elem["material_facts"],
                "Material evidence differs between programs"
            );
        } else {
            earlier = Some(elem["material_facts"].clone());
        }
        let derived = demo.lookup(soft, "derived_result", &full, &transfer, 0)?;
        let calc = &derived["elements"][0]["project_fields"]["derived_result"]["calculations"];
        let mass = calc["mass"]["value"].as_f64().context("Missing mass")?;
        ensure!((mass - 25.2).abs() < 0.0001, "Unexpected mass");
        let mut project = vec![];
        for field in ["model_binding", "material_selection", "model_quantity"] {
            let report = demo.lookup(soft, field, &facts_only, &transfer, 0)?;
            let entry = &report["elements"][0]["project_fields"][field];
            ensure!(entry.is_object(), "Missing project field: {field}");
            project.push(field);
        }
        let invalid = demo.lookup(soft, "service_life_value", &facts_only, &stale, 2)?;
        ensure!(
            invalid["elements"][0]["material_facts"].is_null()
                && invalid["warnings"]
                    .as_array()
                    .is_some_and(|a| a.iter().any(|v| v["code"] == "model_changed")),
            "Stale model received material facts"
        );
        summary["programs"][soft] = json!({"software_version":from_model["software_version"],"model_sha256":from_model["model"]["sha256"],
            "element_id":elem["element_id"],"mass_kg":mass,"verified_project_fields":project,"derived_result_checked":true,"changed_revision":"binding_rejected"});
    }
    summary["service_life_records"]=Value::Array(earlier.unwrap()["records"].as_array().unwrap().iter().map(|r|json!({
        "value":r["value"],"unit":r["unit"],"conditions":r["conditions"],"source_locator":r["source_locator"],
        "source_version_id":r["source_version_id"],"source_url":r["source_url"]})).collect());
    println!("{}", serde_json::to_string_pretty(&summary)?);
    Ok(())
}
