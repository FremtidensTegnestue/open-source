//! Public CLI regression for field meaning, marker handling, and per-material coverage.
use serde_json::{Value, json};
use std::{fs, path::Path, process::Command};

fn run(root: &Path, args: &[&str]) -> Value {
    let o = Command::new(env!("CARGO_BIN_EXE_ft-materials"))
        .current_dir(root)
        .arg("--root")
        .arg(root)
        .args(args)
        .output()
        .unwrap();
    assert!(
        o.status.success(),
        "{args:?}: {}",
        String::from_utf8_lossy(&o.stderr)
    );
    serde_json::from_slice(&o.stdout).unwrap()
}
fn write(path: &Path, value: &Value) {
    fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}

#[test]
fn dictionary_and_real_evidence_use_the_same_subjects() {
    let tmp = tempfile::tempdir().unwrap();
    let root = tmp.path();
    let fields = run(root, &["fields"]);
    let dictionary = fields["fields"].as_array().unwrap();
    assert_eq!(dictionary.len(), 158);
    let ids = dictionary
        .iter()
        .map(|f| f["field_id"].as_str().unwrap())
        .collect::<std::collections::HashSet<_>>();
    assert_eq!(ids.len(), 158);
    assert!(
        dictionary
            .iter()
            .all(|f| !f["definition"].as_str().unwrap().is_empty())
    );
    let p = root.join("data/parquet");
    fs::create_dir_all(&p).unwrap();
    let seed = Path::new(env!("CARGO_MANIFEST_DIR")).join("data/parquet");
    let mut manifest: Value =
        serde_json::from_slice(&fs::read(seed.join("manifest.json")).unwrap()).unwrap();
    manifest["files"]
        .as_array_mut()
        .unwrap()
        .retain(|f| f["path"] == "build_info.parquet");
    for (t, entry) in manifest["tables"].as_object_mut().unwrap() {
        if t != "build_info" {
            entry["rows"] = json!(0);
            entry["partitions"] = json!({});
        }
    }
    fs::copy(
        seed.join("build_info.parquet"),
        p.join("build_info.parquet"),
    )
    .unwrap();
    write(&p.join("manifest.json"), &manifest);
    let folder = root.join("wood");
    fs::create_dir(&folder).unwrap();
    write(
        &folder.join("summary.json"),
        &json!({"dataset":"wood","sources":1,"materials":2,"observations":2}),
    );
    write(
        &folder.join("sources.jsonl"),
        &json!({"id":"s","title":"Table","publisher":"Fixture","url":"https://example.org/table",
        "local_path":"fixture.txt","sha256":"0".repeat(64),"retrieved_at":"2026-01-01","license":"Fixture terms unspecified","license_status":"unknown"}),
    );
    let materials=["wood:a","wood:b"].map(|id|json!({"id":id,"name":"Same oak","category":"wood","kind":"generic","source_id":"s","source_locator":id}).to_string());
    fs::write(folder.join("materials.jsonl"), materials.join("\n")).unwrap();
    let obs=[("a",json!(0),"0","reported"),("b",Value::Null,"NPD","source_marker")].map(|(id,v,text,status)|
        json!({"id":id,"material_id":"wood:a","property":"shrinkage_radial","unit":"%","value":v,"value_text":text,
            "data_status":status,"source_id":"s","source_locator":format!("table/{id}")}).to_string());
    fs::write(folder.join("observations.jsonl"), obs.join("\n")).unwrap();
    // First build has the same on-disk schema as earlier editions without facts.
    let old = run(root, &["build", "--supplement", "wood"]);
    let page = run(
        root,
        &[
            "facts",
            "wood:a",
            "--field",
            "shrinkage_total",
            "--limit",
            "1",
        ],
    );
    assert_eq!(page["fields"][0]["reported"], 1);
    assert_eq!(page["fields"][0]["explicit_missing"], 1);
    assert_eq!(page["records"][0]["value"].as_f64(), Some(0.0));
    assert_eq!(page["next_offset"], 1);
    let page2 = run(
        root,
        &[
            "facts",
            "wood:a",
            "--field",
            "shrinkage_total",
            "--offset",
            "1",
        ],
    );
    assert!(page2["records"][0]["value"].is_null());
    assert_eq!(page2["records"][0]["value_text"], "NPD");
    assert_eq!(page2["records"][0]["status"], "explicit_missing");
    assert_eq!(page2["records"][0]["source_locator"], "table/b");

    write(
        &folder.join("facts.jsonl"),
        &json!({"id":"service-a","material_id":"wood:a","field_id":"service_life_value","source_id":"s",
        "source_locator":"table/lifetime","value":25,"unit":"years","value_status":"reported","conditions":{"basis":"sample scenario","application":"floor boards"}}),
    );
    run(root, &["build", "--supplement", "wood"]);
    let life = run(root, &["facts", "wood:a", "--field", "service_life_value"]);
    assert_eq!(life["records"][0]["value"], 25);
    assert_eq!(life["edition_catalog_sha256"], fields["catalog_sha256"]);
    assert_eq!(life["catalog_sha256"], fields["catalog_sha256"]);
    assert_eq!(
        run(root, &["facts", "wood:a", "--field", "intended_use"])["records"][0]["value"],
        "floor boards"
    );
    assert_eq!(life["records"][0]["conditions"]["basis"], "sample scenario");
    let old_life = run(
        root,
        &[
            "--snapshot",
            old["snapshot"].as_str().unwrap(),
            "facts",
            "wood:a",
            "--field",
            "service_life_value",
        ],
    );
    assert_eq!(old_life["fields"][0]["status"], "not_recorded");
    assert!(old_life["edition_catalog_sha256"].is_null());
    assert_eq!(old_life["catalog_sha256"], fields["catalog_sha256"]);
    let coverage = run(root, &["coverage", "--field", "shrinkage_total"]);
    let f = &coverage["fields"][0];
    assert_eq!(coverage["subject_count"], 2);
    assert_eq!(f["subjects_reported"], 1);
    assert_eq!(f["subjects_explicit_missing"], 1);
    assert_eq!(f["subjects_not_recorded"], 1);

    let b = run(
        root,
        &[
            "coverage",
            "--field",
            "service_life_value",
            "--material",
            "wood:b",
        ],
    );
    assert_eq!(b["fields"][0]["subjects_not_recorded"], 1);
    assert_eq!(b["fields"][0]["subjects_reported"], 0);
    let pair = root.join("field-sources");
    fs::create_dir(&pair).unwrap();
    write(
        &pair.join("summary.json"),
        &json!({"dataset":"field-sources","materials":1,"sources":1,"observations":1,"facts":1}),
    );
    write(
        &pair.join("sources.jsonl"),
        &json!({"id":"p","title":"Other table","publisher":"Fixture","url":"https://example.org/other",
        "local_path":"other.txt","sha256":"1".repeat(64),"retrieved_at":"2026-01-01","license":"Fixture","license_status":"unknown"}),
    );
    write(
        &pair.join("materials.jsonl"),
        &json!({"id":"paired","name":"Oak board","category":"wood","kind":"product","entity_kind":"specimen","source_id":"p","source_locator":"row1"}),
    );
    write(
        &pair.join("facts.jsonl"),
        &json!({"id":"d1","material_id":"paired","field_id":"density","source_id":"p","source_locator":"D1",
        "value":570,"unit":"kg/m3","value_status":"measured","conditions":{"evidence_type":"measurement"}}),
    );
    write(
        &pair.join("observations.jsonl"),
        &json!({"id":"d1:observation","material_id":"paired","property":"density","source_id":"p",
        "source_locator":"D1","value":570,"unit":"kg/m3","value_text":"570","data_status":"reported"}),
    );
    run(
        root,
        &[
            "build",
            "--supplement",
            "wood",
            "--supplement",
            "field-sources",
        ],
    );
    let paired = run(root, &["facts", "paired", "--field", "density"]);
    assert_eq!(paired["total_records"], 1);
    assert_eq!(paired["records"][0]["value"], 570);
    assert_eq!(paired["records"][0]["observation_id"], "d1:observation");
    let pair_meta = run(root, &["facts", "paired", "--field", "reported_value"]);
    assert_eq!(pair_meta["total_records"], 1);
    let pair_count = run(
        root,
        &["coverage", "--material", "paired", "--field", "density"],
    );
    assert_eq!(pair_count["fields"][0]["subjects_reported"], 1);
}
