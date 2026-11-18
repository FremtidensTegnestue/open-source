//! Reviewed projections of legacy source records. The original property, basis and locator travel with the value.
use super::{ALIASES, FIELDS, INDEX};
use serde_json::{Value, json};

pub const PRESENT: u8 = 1;
pub const MISSING: u8 = 2;
pub const INAPPLICABLE: u8 = 4;
pub const CONFLICT: u8 = 8;

pub fn state(status: &str) -> u8 {
    match status {
        "reported" | "classified" | "declared" | "measured" | "estimated" | "derived"
        | "scenario" | "calculated" => PRESENT,
        "not_applicable" => INAPPLICABLE,
        "conflicting" | "conflict" => CONFLICT,
        _ => MISSING,
    }
}

pub fn status(bits: u8) -> &'static str {
    if bits & CONFLICT != 0 {
        "conflicting"
    } else if bits & PRESENT != 0 {
        "reported"
    } else if bits & MISSING != 0 {
        "explicit_missing"
    } else if bits & INAPPLICABLE != 0 {
        "not_applicable"
    } else {
        "not_recorded"
    }
}

pub const MATERIAL_COLUMNS: &str = "m.id,m.name,m.dataset_id,m.entity_kind,m.category,m.family_id,
 m.lineage_id,m.aliases_json,m.source_id,m.source_locator,m.source_url,m.source_version_id,
 s.title,s.publisher,s.license,s.license_status,
 json_extract(m.metadata_json,'$.source_fields') AS source_fields_json,
 json_extract(m.metadata_json,'$.declaration') AS declaration_json,
 json_extract(s.metadata_json,'$.description') AS source_description";

fn filled(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::String(s) => !matches!(s.trim(), "" | "-" | "?"),
        Value::Object(o) => !o.is_empty(),
        Value::Array(a) => !a.is_empty(),
        _ => true,
    }
}

pub fn material_values(m: &Value, edition: &str) -> Vec<(&'static str, Value)> {
    let mut out = vec![
        (
            "subject_id",
            json!({"id":m["id"],"dataset":m["dataset_id"],"lineage_id":m["lineage_id"]}),
        ),
        ("subject_kind", m["entity_kind"].clone()),
        ("names", json!({"name":m["name"],"aliases":m["aliases"]})),
        (
            "source_document",
            json!({"id":m["source_id"],"title":m["title"],"publisher":m["publisher"],"url":m["source_url"],"version":m["source_version_id"]}),
        ),
        ("edition_id", json!(edition)),
    ];
    if filled(&m["category"]) && m["category"] != "unknown" {
        out.push(("classifications",json!({"system":"catalogue family","category":m["category"],"family_id":m["family_id"]})));
    }
    if filled(&m["source_locator"]) {
        out.push(("source_locator", m["source_locator"].clone()));
    }
    if filled(&m["license_status"]) || filled(&m["license"]) {
        out.push((
            "validity_and_rights",
            json!({"license_status":m["license_status"],"license":m["license"]}),
        ));
    }
    if m["dataset_id"] == "tampere" && filled(&m["source_fields"]["manufacturer"]) {
        out.push((
            "product_identity",
            json!({"manufacturer":m["source_fields"]["manufacturer"],
            "tested_product":m["name"],"specimen_id":m["source_fields"]["id"]}),
        ));
    }
    if m["dataset_id"] == "epd-danmark" && filled(&m["declaration"]["declaration_number"]) {
        out.push(("declaration_metadata", m["declaration"].clone()));
    }
    if m["dataset_id"] == "environmental"
        && let Some(v) = m["source_description"]
            .as_str()
            .and_then(|s| serde_json::from_str::<Value>(s).ok())
        && filled(&v["regNo"])
        && filled(&v["programOperator"])
    {
        out.push((
            "declaration_metadata",
            json!({"registration":v["regNo"],"dataset_version":v["dataset_version"],
            "program_operator":v["programOperator"],"dataset_owner":v["owner"]}),
        ));
    }
    out
}

// Shared predicates for both detailed lookup and the global count. Checking the reference
// flow avoids assigning a constituent exchange's density to its enclosing product.
pub const OBS_FLAGS: &str = "
 (CASE WHEN nullif(o.declared_unit,'') IS NOT NULL THEN 1 ELSE 0 END) +
 (CASE WHEN nullif(o.module,'') IS NOT NULL THEN 2 ELSE 0 END) +
 (CASE WHEN nullif(o.method,'') IS NOT NULL OR nullif(o.basis,'') IS NOT NULL OR o.conditions_json NOT IN ('','{}','null') THEN 4 ELSE 0 END) +
 (CASE WHEN o.dataset_id='environmental' AND instr(o.source_locator,'/materialProperties/')>0
      THEN CASE WHEN json_extract(o.conditions_json,'$.reference_flow')=1 THEN 0 ELSE 8 END ELSE 0 END) +
 (CASE WHEN o.dataset_id='ens-varme' AND json_extract(o.conditions_json,'$.estimate_kind') IN ('ctrl','lower','upper')
       THEN 16 ELSE 0 END) +
 (CASE WHEN o.dataset_id='tampere' AND json_type(o.conditions_json,'$.workbook_evidence.values')='text'
       THEN 32 ELSE 0 END) +
 (CASE WHEN o.dataset_id='technical' AND o.property='liquid_transport_coefficient' AND o.unit='m2/s'
       AND json_extract(o.conditions_json,'$.idf_object_type') IN ('MaterialProperty:HeatAndMoistureTransfer:Suction',
             'MaterialProperty:HeatAndMoistureTransfer:Redistribution')
       AND json_extract(o.conditions_json,'$.curve_point.x_unit')='kg/m3' THEN 64 ELSE 0 END)";

fn evidence_type(ds: &str) -> Option<&'static str> {
    match ds {
        "technical" => Some("simulation_input"),
        "wood" => Some("published_handbook_table"),
        "ens-varme" => Some("published_technology_scenario"),
        "br18" => Some("published_reference_factor"),
        "environmental" => Some("published_lifecycle_dataset"),
        "epd-danmark" => Some("publisher_declaration"),
        "tampere" => Some("published_study_record"),
        _ => None,
    }
}

/// Return the field codes applicable to an observation; original values can be missing
/// even when its provenance and method are documented.
pub fn observation_fields(
    ds: &str,
    prop: &str,
    flags: i64,
    value_state: u8,
    mut emit: impl FnMut(&'static str, u8),
) {
    for key in [
        "observation_id",
        "property_definition",
        "value_status",
        "source_document",
        "source_locator",
    ] {
        emit(key, PRESENT);
    }
    emit("reported_value", value_state);
    if evidence_type(ds).is_some() {
        emit("evidence_type", PRESENT);
    }
    if flags & 4 != 0 {
        emit("method_and_conditions", PRESENT);
    }
    if flags & 1 != 0 {
        emit("reference_quantity", PRESENT);
        if matches!(ds, "environmental" | "epd-danmark" | "br18") {
            emit("lca_reference", PRESENT);
        }
    }
    if flags & 2 != 0 && matches!(ds, "environmental" | "epd-danmark" | "br18") {
        emit("lifecycle_module", PRESENT);
    }
    if flags & 16 != 0 && value_state == PRESENT {
        emit("statistical_basis", PRESENT);
    }
    if flags & 32 != 0 {
        emit("verification", PRESENT);
    }
    if flags & 64 != 0 {
        emit("liquid_moisture_diffusivity", value_state);
    }
    if flags & 8 != 0 {
        return;
    }
    if let Some(id) = ALIASES.get(&(ds, prop)) {
        emit(id, value_state);
    } else if let Some(idx) = INDEX.get(prop) {
        let f = &FIELDS[*idx];
        // Only directly project named physical and performance observations. Identity,
        // workflow, evidence metadata and project fields have separate typed producers.
        if matches!(
            f.group,
            "Geometri og fysik"
                | "Fugt og vand"
                | "Varme og energi"
                | "Mekanik og holdbarhed"
                | "Brand"
                | "Lyd"
                | "Lys og overflade"
        ) {
            emit(f.field_id, value_state);
        }
    }
}

// The field-sources collector emits one optional numeric representation of a first-class
// fact for the legacy calculation API. Only collapse the collector's exact paired IDs.
pub const OBS_IS_PRIMARY: &str = "(o.dataset_id!='field-sources' OR NOT EXISTS(
    SELECT 1 FROM catalog_facts f WHERE f.id=substr(o.id,1,length(o.id)-12)
      AND o.id=f.id||':observation' AND f.material_id=o.material_id AND f.field_id=o.property
      AND f.source_id=o.source_id AND f.source_locator=o.source_locator))";

pub const FACT_METADATA: &[&str] = &[
    "observation_id",
    "property_definition",
    "value_status",
    "source_document",
    "source_locator",
    "reported_value",
    "method_and_conditions",
    "evidence_type",
    "statistical_basis",
    "intended_use",
];

pub const FACT_FLAGS: &str =
    "(CASE WHEN f.conditions_json NOT IN ('{}','null','') THEN 1 ELSE 0 END) +
  (CASE WHEN json_type(f.conditions_json,'$.evidence_type')='text' THEN 2 ELSE 0 END) +
 (CASE WHEN f.field_id='chemical_constituent' AND json_type(f.conditions_json,'$.uncertainty') IN ('integer','real')
       AND json_type(f.conditions_json,'$.uncertainty_type')='text'
       AND json_type(f.conditions_json,'$.uncertainty_unit')='text' THEN 4 ELSE 0 END) +
 (CASE WHEN f.field_id='service_life_value' AND json_type(f.conditions_json,'$.application')='text'
            OR f.field_id='installation_conditions' AND json_extract(f.conditions_json,'$.evidence_type')='conditional classification without testing'
            AND json_type(f.conditions_json,'$.scope')='text' THEN 8 ELSE 0 END)";

pub fn fact_fields(
    field: &'static str,
    flags: i64,
    value_state: u8,
    mut emit: impl FnMut(&'static str, u8),
) {
    emit(field, value_state);
    for &key in FACT_METADATA {
        if key == field
            || (key == "method_and_conditions" && flags & 1 == 0)
            || (key == "evidence_type" && flags & 2 == 0)
            || (key == "statistical_basis" && flags & 4 == 0)
            || (key == "intended_use" && flags & 8 == 0)
        {
            continue;
        }
        emit(
            key,
            if key == "reported_value" {
                value_state
            } else {
                PRESENT
            },
        );
    }
}

pub fn fact_value(key: &str, f: &Value) -> Value {
    if f["field_id"] == key {
        return f["value"].clone();
    }
    match key {
        "observation_id" => f["id"].clone(),
        "property_definition" => f["field_id"].clone(),
        "value_status" => f["value_status"].clone(),
        "source_locator" => f["source_locator"].clone(),
        "source_document" => {
            json!({"id":f["source_id"],"url":f["source_url"],"version":f["source_version_id"]})
        }
        "method_and_conditions" => f["conditions"].clone(),
        "evidence_type" => f["conditions"]["evidence_type"].clone(),
        "statistical_basis" => {
            json!({"uncertainty":f["conditions"]["uncertainty"],"uncertainty_type":f["conditions"]["uncertainty_type"],
            "uncertainty_unit":f["conditions"]["uncertainty_unit"],"original_text":f["conditions"]["source_uncertainty_text"]})
        }
        "intended_use" => {
            if f["field_id"] == "installation_conditions" {
                json!({"classification_scope":f["conditions"]["scope"],"end_use_condition":f["conditions"]["end_use_condition"]})
            } else {
                f["conditions"]["application"].clone()
            }
        }
        _ => f["value"].clone(),
    }
}

pub fn observation_value(id: &str, o: &Value) -> Value {
    match id {
        "observation_id" => o["id"].clone(),
        "property_definition" => {
            json!({"property_id":o["property_id"],"raw_property":o["property"]})
        }
        "value_status" => o["data_status"].clone(),
        "source_document" => {
            json!({"id":o["source_id"],"url":o["source_url"],"version":o["source_version_id"]})
        }
        "source_locator" => o["source_locator"].clone(),
        "reference_quantity" | "lca_reference" => {
            json!({"declared_unit":o["declared_unit"],"basis":o["basis"],
            "declared_amount":o["conditions"]["declared_amount"],"reference_amount":o["conditions"]["reference_amount"],
            "declared_references":o["conditions"]["declared_references"]})
        }
        "lifecycle_module" => o["module"].clone(),
        "statistical_basis" => {
            json!({"workbook_estimate_kind":o["conditions"]["estimate_kind"],"projection_year":o["conditions"]["projection_year"]})
        }
        "verification" => {
            json!({"method":"comparison of primary JSON and original workbook values and units",
            "result":"identical","workbook_cells":o["conditions"]["workbook_evidence"]})
        }
        "evidence_type" => json!(evidence_type(o["dataset_id"].as_str().unwrap_or(""))),
        "method_and_conditions" => {
            json!({"method":o["method"],"basis":o["basis"],"conditions":o["conditions"]})
        }
        _ => {
            if state(o["data_status"].as_str().unwrap_or("")) != PRESENT {
                Value::Null
            } else if !o["structured_value"].is_null() {
                o["structured_value"].clone()
            } else if !o["value"].is_null() {
                o["value"].clone()
            } else {
                o["value_text"].clone()
            }
        }
    }
}
