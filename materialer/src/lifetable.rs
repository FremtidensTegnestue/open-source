//! The four separate levels of the BUILD 2021 reference table, obtained from the publisher.
use crate::store::{file_hash, write_stream};
use anyhow::{Context, Result, ensure};
use calamine::{Data, DataType, Reader, Xlsx};
use serde_json::{Value, json};
use std::{
    fs::{self, File},
    io::BufReader,
    path::{Path, PathBuf},
    time::Duration,
};

const BOOK: &str =
    "https://vbn.aau.dk/ws/portalfiles/portal/568162944/BUILD_levetidstabel_december_2021.xlsx";
const SHA: &str = "b7d4d9053d39c4ac64732d0e7176de47732ff418b0a8977978be0e3fd7963936";
const SID: &str = "build-levetid:source:2021-xlsx";
const LOCAL: &str = "data/raw/build-levetid/2021.xlsx";
fn original(root: &Path, offline: bool) -> Result<PathBuf> {
    let path = root.join(LOCAL);
    if !path.exists() {
        ensure!(!offline, "Original XLSX missing in offline mode");
        let parent = path.parent().context("Missing original directory")?;
        fs::create_dir_all(parent)?;
        let mut temp = tempfile::NamedTempFile::new_in(parent)?;
        reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(90))
            .build()?
            .get(BOOK)
            .send()?
            .error_for_status()?
            .copy_to(temp.as_file_mut())?;
        ensure!(
            file_hash(temp.path())? == SHA,
            "Publisher workbook differs from locked version"
        );
        if let Err(e) = temp.persist_noclobber(&path) {
            ensure!(
                e.error.kind() == std::io::ErrorKind::AlreadyExists,
                "Failed to archive original: {e}"
            );
        }
    }
    ensure!(
        file_hash(&path)? == SHA,
        "Original workbook checksum differs"
    );
    Ok(path)
}
fn col(index: usize) -> String {
    if index < 26 {
        return char::from(b'A' + index as u8).to_string();
    }
    format!("A{}", char::from(b'A' + (index - 26) as u8))
}
fn label(row: &[Data], index: usize) -> String {
    row.get(index)
        .map(ToString::to_string)
        .unwrap_or_default()
        .trim()
        .to_owned()
}
pub fn collect(root: &Path, offline: bool) -> Result<Value> {
    let mut book = Xlsx::new(BufReader::new(File::open(original(root, offline)?)?))?;
    let expected = [
        "Bygningstyper",
        "Hovedgrupper SfB",
        "Hovedbygningsdele SfB",
        "Bygningsdele SfB",
    ];
    ensure!(
        book.sheet_names() == expected,
        "Unexpected BUILD table layout"
    );
    let mut subjects = Vec::new();
    let mut facts = Vec::new();
    let mut by_level = serde_json::Map::new();
    let mut numeric = 0;
    for (level, sheet) in expected.iter().enumerate() {
        let range = book.worksheet_range(sheet)?;
        ensure!(range.start() == Some((0, 0)), "Unexpected table origin");
        let rows = range.rows().collect::<Vec<_>>();
        let start = if level == 0 { 2 } else { 5 };
        let mut count = 0;
        for (i, row) in rows.iter().enumerate().skip(if level == 0 { 1 } else { 3 }) {
            for (j, v) in row.iter().enumerate().skip(start) {
                if v.is_empty() {
                    continue;
                }
                let (amount, status) = if v.is_int() || v.is_float() {
                    numeric += 1;
                    (json!(v.as_f64()), "reported")
                } else {
                    ensure!(
                        v.as_string().as_deref() == Some("Ikke relevant"),
                        "Unknown lifetime marker {v}"
                    );
                    (Value::Null, "not_applicable")
                };
                // Three labelled group rows in the detailed sheet also contain published values.
                let (code_idx, name_idx) = if level == 0 || level == 1 {
                    (0, 1)
                } else if level == 2 || label(row, 4).is_empty() {
                    (1, 2)
                } else {
                    (3, 4)
                };
                let subject_name = label(row, name_idx);
                ensure!(
                    !subject_name.is_empty(),
                    "Missing subject for {sheet} at row {}",
                    i + 1
                );
                let column = if level == 0 {
                    String::new()
                } else {
                    label(rows[1], j)
                };
                let address = format!("{}{}", col(j), i + 1);
                let loc = format!("'{sheet}'!{address}");
                let id = format!("build-levetid:2021:l{}:{address}", level + 1);
                let name = if column.is_empty() {
                    subject_name.clone()
                } else {
                    format!("{subject_name} · {column}")
                };
                let conditions = json!({"version":"2021-12","geography":"DK","table_level":sheet,"subject":subject_name,
                    "classification_system":if level==0 {"BBR"}else{"SfB"},"classification_code":label(row,code_idx),
                    "material_column":column,"material_classification":if level>0 {label(rows[2],j)}else{String::new()},
                    "statistic":"middel","source_term":"Middellevetid","reference_scope":"generic_building_or_component"});
                subjects.push(json!({"id":id,"name":name,"kind":"generic","entity_kind":if level==0{"building_reference"}else{"building_component_reference"},
                    "category":"service_life_reference","aliases":[subject_name,column],"source_id":SID,"source_locator":loc}));
                let mut fact = json!({"id":format!("{id}:years"),"material_id":id,"field_id":"service_life_value","value":amount,"unit":"år",
                    "conditions":conditions,"value_status":status,"source_id":SID,"source_locator":loc});
                if amount.is_null() {
                    fact["missing_reason"] = json!("Ikke relevant");
                }
                facts.push(fact);
                facts.push(json!({"id":format!("{id}:type"),"material_id":id,"field_id":"service_life_type","value":"Middellevetid","unit":null,
                    "conditions":conditions,"value_status":"reported","source_id":SID,"source_locator":if level==0{format!("'{sheet}'!C1")}else{format!("'{sheet}'!G1")}}));
                count += 1;
            }
        }
        by_level.insert(sheet.to_string(), count.into());
    }
    let dir = root.join("data/staging/build-levetid");
    fs::create_dir_all(&dir)?;
    let source = json!({"id":SID,"title":"BUILD levetidstabel, version 2021, regneark fra december 2021","publisher":"BUILD, Aalborg Universitet",
        "attribution":"Kim Haugbølle, Vania Mahdi, Martin Morelli, Haseebullah Wahedi","url":BOOK,"retrieved_at":"2026-11-18","local_path":LOCAL,"sha256":SHA,
        "media_type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","license":"University portal general rights, local study/research. No redistribution of the table.","license_status":"restricted",
        "publication_url":"https://vbn.aau.dk/da/publications/build-levetidstabel-version-2021/"});
    let summary = json!({"dataset":"build-levetid","sources":1,"materials":subjects.len(),"observations":0,"facts":facts.len(),
        "numeric_lifetimes":numeric,"not_applicable":subjects.len()-numeric,"subjects_by_sheet":by_level});
    write_stream(&dir.join("sources.jsonl"), &[source])?;
    write_stream(&dir.join("materials.jsonl"), &subjects)?;
    write_stream(&dir.join("observations.jsonl"), &[])?;
    write_stream(&dir.join("facts.jsonl"), &facts)?;
    write_stream(&dir.join("summary.json"), std::slice::from_ref(&summary))?;
    Ok(summary)
}
