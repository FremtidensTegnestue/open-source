//! Assess the same pinned material selection on live SolidCraft and BIMCraft geometry.
mod calculation;
mod extract;
mod fields;
mod mesh;
use anyhow::{Context, Result, bail, ensure};
pub(crate) use calculation::validate_gwp_indicator;
pub use calculation::{calculate, normalize};
use clap::ValueEnum;
pub use extract::extract;
pub use fields::{ModelFactsArgs, model_facts};
use rusqlite::Connection;
use serde::Serialize;
use serde_json::{Map, Value, json};
use std::{
    collections::{HashMap, HashSet},
    fs,
    path::{Path, PathBuf},
};

#[derive(Clone, Copy, Debug, ValueEnum, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Software {
    Solidcraft,
    Bimcraft,
}

#[derive(Debug, clap::Args)]
pub struct Args {
    pub model: PathBuf,
    #[arg(long, value_enum)]
    pub software: Software,
    #[arg(long)]
    pub selection: PathBuf,
    #[arg(long)]
    pub transfer: PathBuf,
    #[arg(long)]
    pub mesh_quantities: bool,
}
fn read(path: &Path) -> Result<Value> {
    Ok(serde_json::from_slice(
        &fs::read(path).with_context(|| path.display().to_string())?,
    )?)
}
fn obj<'a>(v: &'a Value, k: &str) -> Result<&'a Map<String, Value>> {
    v[k].as_object()
        .with_context(|| format!("Expected object: {k}"))
}
fn arr<'a>(v: &'a Value, k: &str) -> Result<&'a Vec<Value>> {
    v[k].as_array()
        .with_context(|| format!("Expected array: {k}"))
}
fn string_id(v: &Value) -> Result<String> {
    match v {
        Value::String(s) if !s.is_empty() => Ok(s.to_owned()),
        Value::Number(n) if n.is_u64() => Ok(n.to_string()),
        _ => bail!("Invalid element ID"),
    }
}

fn map_elements<'a>(
    extract: &Value,
    transfer: &Value,
    selection: &'a Value,
) -> Result<(HashMap<String, &'a Value>, Vec<Value>)> {
    let bim = extract["software"] == "bimcraft";
    let key = if bim {
        "bim_model_sha256"
    } else {
        "cad_model_sha256"
    };
    if transfer[key] != extract["model"]["sha256"] {
        return Ok((HashMap::new(), vec![json!({"code":"model_changed"})]));
    }
    let parts = obj(selection, "parts")?;
    let choices = obj(selection, "materials")?;
    let elements = arr(extract, "elements")?;
    let by_id = elements
        .iter()
        .map(|e| Ok((string_id(&e["id"])?, e)))
        .collect::<Result<HashMap<_, _>>>()?;
    ensure!(by_id.len() == elements.len(), "Duplicate model ID");
    let mut seen = HashSet::new();
    let mut guids = HashSet::new();
    let mut bim_ids = HashSet::new();
    let mut bindings = HashMap::new();
    let mut issues = vec![];
    for row in arr(transfer, "parts")? {
        let part = calculation::text(row, "source_body")?;
        let bim_id = string_id(&row["bim_element_id"])?;
        let guid = calculation::text(row, "bim_guid")?;
        let id = if bim {
            bim_id.clone()
        } else {
            format!("solidcraft:{part}")
        };
        if !parts.contains_key(part)
            || !seen.insert(part)
            || !bim_ids.insert(bim_id)
            || !guids.insert(guid)
        {
            issues.push(json!({"code":"ambiguous_part_map","part":part}));
            continue;
        }
        let Some(elem) = by_id.get(&id) else {
            issues.push(json!({"code":"element_missing","part":part,"element_id":id}));
            continue;
        };
        if bim && (elem["source_ref"]["guid"] != guid || elem["source_ref"]["family_name"] != part)
        {
            issues.push(json!({"code":"bim_identity_mismatch","part":part}));
            continue;
        }
        let choice_name = parts[part].as_str().context("Invalid choice name")?;
        let choice = choices
            .get(choice_name)
            .context("Part refers to unknown material choice")?;
        if row
            .get("material_id")
            .is_some_and(|v| *v != choice["material_id"])
        {
            issues.push(json!({"code":"material_selection_changed","part":part}));
            continue;
        }
        bindings.insert(id, choice);
    }
    if bindings.len() != by_id.len() || seen.len() != parts.len() {
        let mut missing = by_id
            .keys()
            .filter(|id| !bindings.contains_key(*id))
            .collect::<Vec<_>>();
        missing.sort();
        let absent = parts
            .keys()
            .filter(|p| !seen.contains(p.as_str()))
            .collect::<Vec<_>>();
        issues.push(json!({"code":"part_inventory_changed","unmapped_element_ids":missing,"missing_parts":absent}));
    }
    if !issues.is_empty() {
        bindings.clear();
    }
    Ok((bindings, issues))
}

fn selected(db: &Connection, choices: &Map<String, Value>) -> Result<Value> {
    let mut result = Map::new();
    for choice in choices.values() {
        let material = calculation::text(choice, "material_id")?;
        let mut ids = Vec::new();
        if let Some(v) = choice.get("density_observation_id") {
            ids.push(v);
        }
        if let Some(v) = choice.get("gwp_observation_ids") {
            ids.extend(v.as_array().context("Expected GWP ID list")?);
        }
        if let Some(v) = choice.get("moisture") {
            ids.push(&v["coefficient_observation_id"]);
        }
        ensure!(
            !ids.is_empty(),
            "A material selection requires explicit observations"
        );
        for id in ids {
            let id = id.as_str().context("Expected observation ID")?;
            result.insert(id.to_owned(), calculation::observation(db, material, id)?);
        }
    }
    Ok(Value::Object(result))
}

fn unavailable(error: anyhow::Error) -> Value {
    json!({"status":"unavailable","message":error.to_string()})
}

fn computed(element: &Value, choice: &Value, refs: &Value) -> Result<(Value, bool)> {
    let label = calculation::text(choice, "model_material_name")?;
    ensure!(element["material_name"] == label, "material_label_changed");
    calculation::text(choice, "selection_note").context("selection_note_missing")?;
    let ops = choice
        .get("operations")
        .cloned()
        .unwrap_or_else(|| json!(["mass", "climate"]));
    let ops = ops
        .as_array()
        .filter(|ops| !ops.is_empty())
        .context("Missing calculations")?;
    ensure!(
        ops.iter()
            .all(|v| matches!(v.as_str(), Some("mass" | "climate" | "moisture"))),
        "Unsupported operation"
    );
    let mut results = json!({});
    let mut complete = true;
    let mass = || -> Result<Value> {
        let density = calculation::text(choice, "density_observation_id")?;
        let vol = element["volume_m3"]
            .as_f64()
            .filter(|v| *v > 0.)
            .context("missing_volume")?;
        let mut m = calculation::mass(&refs[density], &json!({"value":vol,"unit":"m3"}))?;
        if let Some(round) = element["source_ref"]["volume_rounding_increment_m3"].as_f64() {
            m["model_quantity_rounding_bound_kg"] =
                json!(m["inputs"]["density_normalized"]["value"].as_f64().unwrap() * round / 2.);
        }
        Ok(m)
    };
    let measured_mass = mass().unwrap_or_else(unavailable);
    if ops.iter().any(|v| v == "mass") {
        complete &= measured_mass["status"] == "ok";
        results["mass"] = measured_mass.clone();
    }
    if ops.iter().any(|v| v == "climate") {
        let calc = |id: &str| -> Result<Value> {
            let basis = calculation::basis(&refs[id])?;
            let quantity = match basis["dimension"].as_str() {
                Some("mass") => measured_mass["value"].as_f64().context("mass_missing")?,
                Some("volume") => element["volume_m3"].as_f64().context("missing_volume")?,
                Some("area") => {
                    calculation::text(choice, "area_basis_note")
                        .context("area_semantics_unconfirmed")?;
                    element["area_m2"].as_f64().context("missing_area")?
                }
                _ => bail!("Unsupported GWP basis"),
            };
            ensure!(quantity > 0.0, "Missing positive model quantity");
            calculation::climate(&refs[id], &json!({"value":quantity,"unit":basis["unit"]}))
        };
        let mut values = vec![];
        for id in choice["gwp_observation_ids"]
            .as_array()
            .into_iter()
            .flatten()
        {
            let mut value = id
                .as_str()
                .context("Missing observation ID")
                .and_then(calc)
                .unwrap_or_else(unavailable);
            complete &= value["status"] == "ok";
            value["observation_id"] = id.clone();
            values.push(value);
        }
        if values.is_empty() {
            complete = false;
            values.push(json!({"status":"unavailable","message":"gwp_binding_missing"}));
        }
        results["climate"] = json!(values);
    }
    if ops.iter().any(|v| v == "moisture") {
        let calc = || -> Result<Value> {
            let mut req = choice["moisture"].clone();
            calculation::text(&req, "orientation_note").context("orientation_missing")?;
            let axis = calculation::text(&req, "dimension_axis")?;
            ensure!(matches!(axis, "x" | "y" | "z"), "dimension_axis_missing");
            req["dimension"] = json!({"value":element["dimensions_m"][axis],"unit":"m"});
            let id = calculation::text(&req, "coefficient_observation_id")?;
            let mut m = calculation::moisture(&refs[id], &req)?;
            m["orientation_note"] = req["orientation_note"].clone();
            Ok(m)
        };
        let m = calc().unwrap_or_else(unavailable);
        complete &= m["status"] == "ok";
        results["moisture"] = m;
    }
    Ok((results, complete))
}
struct BoundInputs {
    model: Value,
    transfer: Value,
    selection: Value,
    transfer_sha: String,
    select_sha: String,
}

fn bound_inputs(args: &Args, snapshot: &str) -> Result<BoundInputs> {
    let select_sha = extract::hash(&args.selection)?;
    let transfer_sha = extract::hash(&args.transfer)?;
    let selection = read(&args.selection)?;
    let transfer = read(&args.transfer)?;
    ensure!(
        select_sha == extract::hash(&args.selection)?
            && transfer_sha == extract::hash(&args.transfer)?,
        "Input changed during read"
    );
    ensure!(
        selection["schema_version"] == 1 && transfer["schema_version"] == 1,
        "Unsupported selection or transfer schema"
    );
    ensure!(
        !snapshot.is_empty() && snapshot != "latest" && selection["snapshot"] == snapshot,
        "Immutable snapshot required"
    );
    ensure!(
        !obj(&selection, "parts")?.is_empty() && !obj(&selection, "materials")?.is_empty(),
        "Empty material selection"
    );
    let model = extract(&args.model, args.software, args.mesh_quantities)?;
    Ok(BoundInputs {
        model,
        transfer,
        selection,
        transfer_sha,
        select_sha,
    })
}
pub fn run(args: Args, db: &Connection, snapshot: &str) -> Result<Value> {
    let BoundInputs {
        model,
        transfer,
        selection,
        transfer_sha,
        select_sha,
    } = bound_inputs(&args, snapshot)?;
    let (bindings, mut issues) = map_elements(&model, &transfer, &selection)?;
    let mut warnings = arr(&model, "warnings")?.clone();
    warnings.append(&mut issues);
    let refs = selected(db, obj(&selection, "materials")?)?;
    let mut rows = Vec::new();
    let mut ok = !bindings.is_empty() && warnings.iter().all(|w| w["severity"] == "notice");
    for e in arr(&model, "elements")? {
        let id = string_id(&e["id"])?;
        let mut row = json!({"element_id":id,"element_name":e["name"],"model_material_name":e["material_name"],"model_quantity_source":e["source_ref"],"calculations":{},"diagnostics":[]});
        let outcome=bindings.get(&id).context("binding_missing").and_then(|choice|{
            row["binding"]=json!({"material_id":choice["material_id"],"selection_note":choice["selection_note"]});
            computed(e,choice,&refs)
        });
        match outcome {
            Ok((calc, complete)) => {
                ok &= complete;
                row["calculations"] = calc;
                row["status"] = json!(if complete { "ok" } else { "partial" })
            }
            Err(err) => {
                ok = false;
                row["status"] = json!("unresolved");
                row["diagnostics"] = json!([{"code":err.to_string()}]);
            }
        }
        rows.push(row);
    }
    Ok(
        json!({"schema_version":1,"snapshot":snapshot,"status":if ok{"ok"}else{"partial"},
         "software":args.software,"software_version":model["software_version"],"model":model["model"],"selection_sha256":select_sha,
         "transfer_sha256":transfer_sha,"selected_observations":refs,"elements":rows,"warnings":warnings}),
    )
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn split_blocks_surviving_original_name() {
        let selection = json!({"parts":{"A":"c"},"materials":{"c":{"material_id":"m"}}});
        let transfer = json!({"cad_model_sha256":"digest","parts":[{"source_body":"A","bim_element_id":1,"bim_guid":"a"},{"source_body":"A (1)","bim_element_id":2,"bim_guid":"b"}]});
        let model = json!({"software":"solidcraft","model":{"sha256":"digest"},"elements":[{"id":"solidcraft:A"},{"id":"solidcraft:A (1)"}]});
        let (b, errors) = map_elements(&model, &transfer, &selection).unwrap();
        assert!(b.is_empty());
        assert!(errors.iter().any(|e| e["code"] == "part_inventory_changed"));
    }
    #[test]
    fn available_volume_based_climate_survives_missing_density() {
        let element = json!({"material_name":"Concrete","volume_m3":2.0});
        let choice = json!({"model_material_name":"Concrete","selection_note":"Reference",
            "operations":["mass","climate"],"gwp_observation_ids":["ok","needs-mass"]});
        let refs = json!({"ok":{"property":"gwp","unit":"kg CO2e","value":5,"module":"A1-A3","declared_unit":"1 m³"},
            "needs-mass":{"property":"gwp","unit":"kg CO2e","value":5,"module":"A1-A3","declared_unit":"1 kg"}});
        let (calculations, complete) = computed(&element, &choice, &refs).unwrap();
        assert!(!complete);
        assert_eq!(calculations["mass"]["status"], "unavailable");
        assert_eq!(calculations["climate"][0]["value"], 10.0);
        assert_eq!(calculations["climate"][1]["status"], "unavailable");
    }
}
