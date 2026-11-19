//! Danish Energy Agency engineering and cost scenarios. Preserve the workbook's cells and units.
use crate::store::{file_hash, hash, write_stream};
use anyhow::{Context, Result, ensure};
use calamine::{Data, DataType, Reader, Xlsx};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    fs::{self, File},
    io::BufReader,
    path::Path,
};

const SHA: &str = "569ad466425116a2a3d7833d22a1fe88f5585eaf1e170e34d7b3eeafaff4f3a0";
const LOCAL: &str = "data/supplements/ens-varme/originals/april-2026.xlsx";
const SID: &str = "ens-varme:source:individual-heating-2026-04";
const URL: &str = "https://ens.dk/media/8518/download";

fn property(name: &str) -> String {
    let id = match name {
        "Heat production capacity for one unit" => "heat_capacity",
        "Heat efficiency (annual average, net)" => "annual_heat_efficiency",
        "Heat efficiency (annual average, net, floor heating)" => "seasonal_floor_efficiency",
        "Technical economic lifetime" => "technoeconomic_lifetime",
        "Auxiliary Electricity consumption" => "auxiliary_electricity",
        "Nominal investment (installation)" | "Nominal investment (installation)**" => {
            "installation_investment"
        }
        "Fixed O&M (*total)" => "fixed_om",
        "Fixed O&M (electricity cost)" => "electricity_om",
        "Fixed O&M (other)" => "other_om",
        "Variable O&M (*total)" => "variable_om",
        _ => {
            return name
                .split(|c: char| !c.is_ascii_alphanumeric())
                .filter(|s| !s.is_empty())
                .map(str::to_ascii_lowercase)
                .collect::<Vec<_>>()
                .join("_");
        }
    };
    id.into()
}
fn cell(row: &[Data], index: usize) -> String {
    row.get(index)
        .map(ToString::to_string)
        .unwrap_or_default()
        .trim()
        .to_owned()
}
pub fn collect(root: &Path) -> Result<Value> {
    let path = root.join(LOCAL);
    ensure!(file_hash(&path)? == SHA, "ENS workbook checksum differs");
    let mut wb = Xlsx::new(BufReader::new(File::open(&path)?))?;
    let sheets = wb
        .sheet_names()
        .into_iter()
        .filter(|name| name.starts_with(|c: char| c.is_ascii_digit()))
        .collect::<Vec<_>>();
    ensure!(sheets.len() == 45, "Expected 45 technology sheets");
    let mut materials = Vec::new();
    let mut observations = Vec::new();
    let mut facts = Vec::new();
    let mut numeric = 0;
    for sheet in sheets {
        let range = wb.worksheet_range(&sheet)?;
        ensure!(
            range.start() == Some((0, 0)),
            "Unexpected workbook coordinates"
        );
        let rows = range.rows().collect::<Vec<_>>();
        let name = cell(rows[0], 2);
        ensure!(
            !name.is_empty() && cell(rows[1], 0) == "year" && cell(rows[2], 0) == "est",
            "Missing headers in {sheet}"
        );
        let id = format!("ens-varme:scenario:{}", &hash(sheet.as_bytes())[..16]);
        let locator = |address: &str| format!("'{sheet}'!{address}");
        materials.push(json!({"id":id,"source_id":SID,"source_locator":locator("C1"),"name":name,"aliases":[sheet],
            "kind":"generic","entity_kind":"technology_scenario","category":"heat_installation","description":"Energistyrelsens repræsentative teknologiscenarie for boligopvarmning."}));
        let mut section = String::new();
        let mut note_definitions = BTreeMap::new();
        let mut references = BTreeMap::new();
        for (i, row) in rows.iter().enumerate() {
            let title = cell(row, 0);
            if !title.is_empty() {
                section = title;
            }
            let label = cell(row, 1);
            if let Some((key, _)) = label.split_once('.') {
                let entry = json!({"locator":locator(&format!("B{}",i+1)),"text":label});
                if section.starts_with("Notes") {
                    note_definitions.insert(key.trim().to_owned(), entry);
                } else if section.starts_with("References") {
                    references.insert(key.trim().to_owned(), entry);
                }
            }
        }
        for (i, row) in rows.iter().enumerate().skip(4) {
            let title = cell(row, 0);
            if title.starts_with("References") || title.starts_with("Notes") {
                break;
            }
            let label = cell(row, 1);
            if label.is_empty() {
                continue;
            }
            let (parameter, unit) = if let Some((key, unit)) = label.rsplit_once('[') {
                (key.trim(), Some(unit.trim_end_matches(']').trim()))
            } else {
                (label.as_str(), None)
            };
            if unit.is_none()
                && !row
                    .iter()
                    .skip(2)
                    .take(9)
                    .any(|c| c.is_float() || c.is_int())
            {
                continue;
            }
            let key = property(parameter);
            let rownum = i + 1;
            let notes = cell(row, 11);
            let refs = cell(row, 12);
            let linked = |text: &str, definitions: &BTreeMap<String, Value>| {
                text.split([',', ';'])
                    .filter_map(|n| definitions.get(n.trim()))
                    .collect::<Vec<_>>()
                    .into_iter()
                    .cloned()
                    .collect::<Vec<_>>()
            };
            let conditions = json!({"geography":"DK","record_type":"technology_scenario","release":"2026-04","worksheet":sheet,
                "parameter":label,"scenario":name,"note_keys":notes,"reference_keys":refs,"notes":linked(&notes,&note_definitions),
                "references":linked(&refs,&references),"cost_price_year":2025});
            if key == "technoeconomic_lifetime" {
                facts.push(json!({"id":format!("{id}:service-type"),"material_id":id,"field_id":"service_life_type","value":"technical_economic_lifetime",
                    "conditions":conditions,"unit":null,"source_id":SID,"source_locator":locator(&format!("B{rownum}")),"value_status":"reported"}));
            }
            for col in 2..=10 {
                let raw = row.get(col).unwrap_or(&Data::Empty);
                let value = match raw {
                    Data::Empty => None,
                    Data::Int(n) => Some(*n as f64),
                    Data::Float(n) if n.is_finite() => Some(*n),
                    _ => anyhow::bail!("Unexpected data {raw:?} in {sheet} row {rownum}"),
                };
                let year = rows[1][col].as_i64().context("Missing year")?;
                let kind = cell(rows[2], col);
                ensure!(
                    matches!(kind.as_str(), "ctrl" | "lower" | "upper"),
                    "Unknown estimate code: {kind}"
                );
                let mut cond = conditions.clone();
                cond["projection_year"] = year.into();
                cond["estimate_kind"] = kind.into();
                let address = format!("{}{rownum}", char::from(b'A' + col as u8));
                let mut obs = json!({"id":format!("{id}:{address}"),"material_id":id,"source_id":SID,"source_locator":locator(&address),"property":key,
                    "unit":unit,"value":value,"value_kind":if value.is_some(){"scalar"}else{"missing"},
                    "value_text":if value.is_some(){raw.to_string()} else {"empty workbook cell".to_owned()},
                    "data_status":if value.is_some(){"estimated"}else{"missing"},"method":"Danish Energy Agency technology scenario, April 2026",
                    "conditions":cond});
                if value.is_none() {
                    obs["conditions"]["missing_reason"] = "empty workbook cell".into();
                } else {
                    numeric += 1;
                }
                observations.push(obs);
            }
        }
    }
    let out = root.join("data/supplements/ens-varme");
    fs::create_dir_all(&out)?;
    let source = json!({"id":SID,"title":"Technology Data for Individual Heating Plants, data sheets, April 2026","publisher":"Energistyrelsen / Danish Energy Agency",
        "url":URL,"retrieved_at":"2026-11-18","local_path":LOCAL,"sha256":SHA,"media_type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "license":"CC BY 4.0","license_status":"verified","license_locator":"Index!C7:C8","license_url":"https://creativecommons.org/licenses/by/4.0/"});
    let summary = json!({"dataset":"ens-varme","materials":materials.len(),"sources":1,"observations":observations.len(),"facts":facts.len(),
        "numeric_estimates":numeric,"empty_estimate_cells":observations.len()-numeric,"version":"April 2026","license":"CC BY 4.0","projection_years":[2025,2030,2035,2040,2050]});
    write_stream(&out.join("sources.jsonl"), &[source])?;
    write_stream(&out.join("materials.jsonl"), &materials)?;
    write_stream(&out.join("observations.jsonl.gz"), &observations)?;
    write_stream(&out.join("facts.jsonl"), &facts)?;
    write_stream(&out.join("summary.json"), std::slice::from_ref(&summary))?;
    Ok(summary)
}
