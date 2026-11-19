//! Resolve field evidence for an explicitly selected component in a pinned project.
use super::*;
use crate::{catalog, store::Edition};

#[derive(clap::Args)]
pub struct ModelFactsArgs {
    #[command(flatten)]
    pub model: Args,
    #[arg(long)]
    field: Option<String>,
    /// Maximum material evidence records per element (1 to 1000).
    #[arg(long, default_value_t = 25)]
    limit: usize,
    #[arg(long, default_value_t = 0)]
    offset: usize,
}

fn project_fields(
    element: &Value,
    choice: &Value,
    args: &ModelFactsArgs,
    inputs: &BoundInputs,
    edition: &Edition,
) -> Result<Value> {
    let mut values = Map::new();
    let wanted = |field: &str| args.field.as_deref().is_none_or(|f| f == field);
    if wanted("model_binding") {
        values.insert("model_binding".into(),json!({"software":args.model.software,"software_version":inputs.model["software_version"],
            "revision_sha256":inputs.model["model"]["sha256"],"transfer_sha256":inputs.transfer_sha,"element_id":element["id"],
            "source_ref":element["source_ref"]}));
    }
    if wanted("material_selection") {
        values.insert(
            "material_selection".into(),
            json!({"snapshot":edition.id,"selection_sha256":inputs.select_sha,"choice":choice}),
        );
    }
    if wanted("model_quantity") {
        let quantities: Map<String, Value> =
            ["volume_m3", "area_m2", "surface_area_m2", "dimensions_m"]
                .into_iter()
                .filter_map(|key| {
                    element
                        .get(key)
                        .filter(|v| !v.is_null())
                        .map(|v| (key.to_string(), v.clone()))
                })
                .collect();
        if !quantities.is_empty() {
            values.insert("model_quantity".into(), json!({"measurements":quantities, "source_ref":element["source_ref"],"revision_sha256":inputs.model["model"]["sha256"]}));
        }
    }
    if wanted("derived_result")
        && ["density_observation_id", "gwp_observation_ids", "moisture"]
            .iter()
            .any(|key| choice.get(key).is_some())
    {
        let choices = Map::from_iter([("selected".to_owned(), choice.clone())]);
        let refs = selected(&edition.db, &choices)?;
        let (calculations, complete) = computed(element, choice, &refs)?;
        values.insert("derived_result".into(),json!({"status":if complete {"ok"} else {"partial"},"calculations":calculations,"selected_observations":refs}));
    }
    Ok(values.into())
}

pub fn model_facts(args: ModelFactsArgs, edition: &Edition) -> Result<Value> {
    if let Some(field) = &args.field {
        ensure!(catalog::is_known(field), "Unknown field {field}");
    }
    ensure!(
        (1..=1000).contains(&args.limit),
        "Limit must be between 1 and 1000"
    );
    let inputs = bound_inputs(&args.model, &edition.id)?;
    let (bindings, issues) = map_elements(&inputs.model, &inputs.transfer, &inputs.selection)?;
    let mut warnings = arr(&inputs.model, "warnings")?.clone();
    warnings.extend(issues);
    let mut complete = !bindings.is_empty()
        && !warnings.iter().any(|w| {
            matches!(
                w["code"].as_str(),
                Some("ifc_import_incomplete" | "bimcraft_model_warning")
            )
        });
    let mut elements = Vec::new();
    for elem in arr(&inputs.model, "elements")? {
        let id = string_id(&elem["id"])?;
        let mut row = json!({"element_id":id,"name":elem["name"]});
        let resolve = || -> Result<(Value, Value)> {
            let choice = bindings.get(&id).context("binding_missing")?;
            let label = calculation::text(choice, "model_material_name")?;
            ensure!(elem["material_name"] == label, "material_label_changed");
            calculation::text(choice, "selection_note").context("selection_note_missing")?;
            let material = calculation::text(choice, "material_id")?;
            let facts = catalog::material_facts(
                edition,
                material,
                args.field.as_deref(),
                args.limit,
                args.offset,
            )?;
            Ok((
                facts,
                project_fields(elem, choice, &args, &inputs, edition)?,
            ))
        };
        match resolve() {
            Ok((facts, context)) => {
                row["status"] = json!("ok");
                row["material_id"] = bindings[&id]["material_id"].clone();
                row["material_facts"] = facts;
                row["project_fields"] = context;
            }
            Err(err) => {
                complete = false;
                row["status"] = json!("unresolved");
                row["diagnostics"] = json!([{"code":err.to_string()}]);
            }
        }
        elements.push(row);
    }
    Ok(
        json!({"snapshot":edition.id,"status":if complete {"ok"}else{"partial"},
        "software":args.model.software,"software_version":inputs.model["software_version"],"model":inputs.model["model"],
        "selection_sha256":inputs.select_sha,"transfer_sha256":inputs.transfer_sha,"elements":elements,"warnings":warnings}),
    )
}
