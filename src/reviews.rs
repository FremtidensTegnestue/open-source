//! Normalize the source's structured ILCD review records from a checksum-pinned foundation.
use crate::store::{self, Edition};
use anyhow::{Context, Result, ensure};
use reqwest::blocking::Client;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, io::Write, path::Path, time::Duration};
use tempfile::NamedTempFile;

const DIR: &str = "data/supplements/oekobaudat-review";
const ORIGINALS: &str = "data/raw/environmental/oekobaudat/processes";
const LICENSE: &str = "Free of charge for all users and uses";
const REVIEWS: &str = "/modellingAndValidation/validation/review";

struct Receipt {
    material: String,
    source: String,
    url: String,
    sha: String,
    path: String,
}

fn original(root: &Path, r: &Receipt, client: Option<&Client>) -> Result<Value> {
    let (uuid, version) = r
        .source
        .strip_prefix("environmental:oekobaudat:")
        .and_then(|s| s.split_once('@'))
        .context("Unrecognized source ID")?;
    ensure!(
        uuid.bytes().all(|c| c.is_ascii_hexdigit() || c == b'-')
            && version.bytes().all(|c| c.is_ascii_digit() || c == b'.'),
        "Invalid process/version identifier"
    );
    ensure!(
        r.material == format!("environmental:material:oekobaudat:{uuid}@{version}"),
        "Material and source identities differ"
    );
    ensure!(
        r.path == format!("{ORIGINALS}/{uuid}_{version}.json"),
        "Unexpected archive location"
    );
    let path = root.join(&r.path);
    let bytes = if path.is_file() {
        fs::read(&path)?
    } else {
        let client=client.with_context(||format!("Missing archived original {}. Use collect-reviews --fetch to retrieve the publisher bytes.",path.display()))?;
        let response = client.get(&r.url).send()?.error_for_status()?.bytes()?;
        ensure!(
            store::hash(&response) == r.sha,
            "Downloaded original checksum mismatch at {}",
            r.url
        );
        let dir = path.parent().context("No archive directory")?;
        fs::create_dir_all(dir)?;
        let mut temp = NamedTempFile::new_in(dir)?;
        temp.write_all(&response)?;
        temp.persist(&path)?;
        response.to_vec()
    };
    ensure!(
        store::hash(&bytes) == r.sha,
        "Original checksum mismatch: {}",
        path.display()
    );
    let doc: Value = serde_json::from_slice(&bytes)?;
    for (pointer, expected) in [
        ("/processInformation/dataSetInformation/UUID", uuid),
        (
            "/administrativeInformation/publicationAndOwnership/dataSetVersion",
            version,
        ),
        (
            "/administrativeInformation/publicationAndOwnership/licenseType",
            LICENSE,
        ),
    ] {
        ensure!(
            doc.pointer(pointer).and_then(Value::as_str) == Some(expected),
            "Publisher identity, version or licence disagrees at {pointer}"
        );
    }
    Ok(doc)
}

// Some ILCD contact captions name individuals or combine names and organizations.
// Only publish explicitly reviewed institutional captions. Every other contact
// remains traceable by the exact source identifier, version and array index.
fn contacts(review: &Value) -> Result<Vec<Value>> {
    let mut result = vec![];
    for c in review["referenceToNameOfReviewerAndInstitution"]
        .as_array()
        .context("Reviewer references missing")?
    {
        let id = store::text(c, "refObjectId")?;
        let mut contact = json!({"id":id,"type":store::text(c,"type")?});
        if let Some(v) = c.get("version").and_then(Value::as_str) {
            contact["version"] = json!(v);
        }
        if let Some(labels) = c["shortDescription"].as_array() {
            let institution = labels
                .iter()
                .filter_map(|s| s.get("value")?.as_str())
                .map(str::trim)
                .find(|s| {
                    matches!(
                        *s,
                        "Institut Bauen und Umwelt e. V."
                            | "Daxner & Merl GmbH"
                            | "Sphera Solutions GmbH"
                            | "Sphera Product Sustainability user forum"
                            | "GaBi user forum"
                            | "Bau EPD GmbH"
                            | "Sphera Product Sustainability bug forum"
                            | "Sphera Product Sustainability user community"
                            | "Kiwa GmbH"
                            | "University of Novi Sad"
                            | "Thünen-Institut für Holzforschung"
                            | "Bundesverband der Gipsindustrie e.V."
                    )
                });
            if let Some(label) = institution {
                contact["institution_name"] = json!(label);
            }
        }
        result.push(contact);
    }
    ensure!(!result.is_empty(), "No reviewer contact references");
    Ok(result)
}

#[derive(Default)]
struct Counts {
    checks: BTreeMap<String, usize>,
    checked: usize,
    documented: usize,
    no_entries: usize,
    untyped: usize,
    not_reviewed: usize,
}

fn extract(doc: &Value, r: &Receipt, out: &mut Vec<Value>, counts: &mut Counts) -> Result<()> {
    let a = match doc.pointer(REVIEWS) {
        None => &[][..],
        Some(v) => v.as_array().context("Expected review array")?.as_slice(),
    };
    counts.checked += 1;
    if a.is_empty() {
        counts.no_entries += 1;
    }
    let before = out.len();
    for (index, entry) in a.iter().enumerate() {
        let scope = match entry.get("type").and_then(Value::as_str) {
            Some(
                v @ ("Independent external review"
                | "Accredited third party review"
                | "Independent review panel"
                | "Dependent internal review"),
            ) => v,
            Some("Not reviewed") => {
                counts.not_reviewed += 1;
                continue;
            }
            None => {
                counts.untyped += 1;
                continue;
            }
            Some(other) => {
                anyhow::bail!("Unrecognized review type {other:?}; check its meaning before import")
            }
        };
        let loc = format!("{REVIEWS}/{index}");
        out.push(json!({
            "id":format!("oekobaudat-review:{}:{index}", r.source),"material_id":r.material,"field_id":"verification",
            "value":{"review_type":scope,"reviewer_references":contacts(entry)?},"unit":null,
            "conditions":{"subject":"declared process dataset","record_type":"structured ILCD review"},
            "source_id":r.source,"source_locator":loc,"value_status":"reported"
        }));
        *counts.checks.entry(scope.to_owned()).or_default() += 1;
    }
    if out.len() > before {
        counts.documented += 1;
    }
    Ok(())
}

pub fn collect(root: &Path, edition: &Edition, fetch: bool) -> Result<Value> {
    let client = if fetch {
        Some(
            Client::builder()
                .user_agent("ft-materials locked source collection")
                .timeout(Duration::from_secs(40))
                .build()?,
        )
    } else {
        None
    };
    let mut query = edition.db.prepare(
        "SELECT m.id,s.id,s.url,s.sha256,s.local_path
        FROM foundation.materials m CROSS JOIN foundation.sources s ON s.id=m.source_id
        WHERE m.dataset_id='environmental'
          AND s.id LIKE 'environmental:oekobaudat:%' AND s.media_type='application/json'
          AND s.license_status='verified' AND s.license=? ORDER BY m.id",
    )?;
    let receipts = query.query_map([LICENSE], |r| {
        Ok(Receipt {
            material: r.get(0)?,
            source: r.get(1)?,
            url: r.get(2)?,
            sha: r.get(3)?,
            path: r.get(4)?,
        })
    })?;
    let mut out = vec![];
    let mut counts = Counts::default();
    let mut receipt_hash = Sha256::new();
    for receipt in receipts {
        let r = receipt?;
        let doc = original(root, &r, client.as_ref())
            .with_context(|| format!("Original {}", r.source))?;
        extract(&doc, &r, &mut out, &mut counts)
            .with_context(|| format!("Reading review in {}", r.source))?;
        for id in [&r.material, &r.source, &r.sha] {
            receipt_hash.update(id.as_bytes());
            receipt_hash.update(b"\n");
        }
    }
    ensure!(
        counts.checked > 0,
        "No eligible source receipts in foundation"
    );
    let summary = json!({"dataset":"oekobaudat-review","facts":out.len(),"sources":0,"materials":0,"observations":0,
        "eligible_source_documents":counts.checked,"materials_with_review":counts.documented,
        "source_documents_without_review_entries":counts.no_entries,"entries_without_type":counts.untyped,
        "entries_declared_not_reviewed":counts.not_reviewed,"review_types":counts.checks,"source_receipts_sha256":hex::encode(receipt_hash.finalize())});
    let dir = root.join(DIR);
    fs::create_dir_all(&dir)?;
    store::write_stream(&dir.join("facts.jsonl.gz"), &out)?;
    for stream in ["sources", "materials", "observations"] {
        store::write_stream(&dir.join(format!("{stream}.jsonl")), &[])?;
    }
    store::write_stream(&dir.join("summary.json"), std::slice::from_ref(&summary))?;
    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_typed_reviews_and_each_contact_without_copying_individual_names() {
        let contact = json!({"type":"contact data set","refObjectId":"contact-1","version":"00.01","shortDescription":[{"value":"Individual verifier"}]});
        let institution = json!({"type":"contact data set","refObjectId":"contact-2","shortDescription":[{"value":"Institut Bauen und Umwelt e. V."}]});
        let doc = json!({"modellingAndValidation":{"validation":{"review":[
            {"type":"Not reviewed","referenceToNameOfReviewerAndInstitution":[contact]},
            {"type":"Independent external review","referenceToNameOfReviewerAndInstitution":[contact,institution]},
            {"referenceToNameOfReviewerAndInstitution":[contact]},
            {"type":"Dependent internal review","referenceToNameOfReviewerAndInstitution":[institution]}
        ]}}});
        let mut counts = Counts::default();
        let mut out = vec![];
        let receipt = Receipt {
            material: "m".into(),
            source: "s".into(),
            url: String::new(),
            sha: String::new(),
            path: String::new(),
        };
        extract(&doc, &receipt, &mut out, &mut counts).unwrap();
        assert_eq!(out.len(), 2);
        assert_eq!(
            (counts.untyped, counts.not_reviewed, counts.documented),
            (1, 1, 1)
        );
        assert_eq!(out[0]["source_locator"], format!("{REVIEWS}/1"));
        let refs = &out[0]["value"]["reviewer_references"];
        assert_eq!(
            refs[0],
            json!({"type":"contact data set","id":"contact-1","version":"00.01"})
        );
        assert_eq!(
            refs[1]["institution_name"],
            "Institut Bauen und Umwelt e. V."
        );
        assert_eq!(out[1]["source_locator"], format!("{REVIEWS}/3"));
        assert_eq!(out[1]["value"]["review_type"], "Dependent internal review");
    }
}
