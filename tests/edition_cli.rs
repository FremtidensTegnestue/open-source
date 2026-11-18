//! Public CLI integration using the real schema and one small Parquet file.
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
};

fn write(path: &Path, value: &Value) {
    fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}

fn foundation(root: &Path) {
    let source = Path::new(env!("CARGO_MANIFEST_DIR")).join("data/parquet");
    let target = root.join("data/parquet");
    fs::create_dir_all(&target).unwrap();
    let mut manifest: Value =
        serde_json::from_slice(&fs::read(source.join("manifest.json")).unwrap()).unwrap();
    // Keep the five table schemas, all index definitions and the real 4.7 KB
    // build_info Parquet. No material facts from the large snapshot are needed.
    manifest["files"]
        .as_array_mut()
        .unwrap()
        .retain(|v| v["path"] == "build_info.parquet");
    assert_eq!(manifest["files"].as_array().unwrap().len(), 1);
    for (table, metadata) in manifest["tables"].as_object_mut().unwrap() {
        if table != "build_info" {
            metadata["rows"] = json!(0);
            metadata["partitions"] = json!({});
        }
    }
    fs::copy(
        source.join("build_info.parquet"),
        target.join("build_info.parquet"),
    )
    .unwrap();
    write(&target.join("manifest.json"), &manifest);
}

fn dataset(root: &Path, name: &str, value: u32, raw_property: &str) -> String {
    let folder = root.join(name);
    fs::create_dir_all(&folder).unwrap();
    let original =
        json!({"material":"Oak test board","properties":{raw_property:value,"thickness":null}});
    let bytes = serde_json::to_vec(&original).unwrap();
    let hash = hex::encode(Sha256::digest(&bytes));
    let source_rel = format!("{name}/original-{hash}.json");
    fs::write(root.join(&source_rel), bytes).unwrap();
    let source_id = format!("{name}:source");
    let material_id = format!("{name}:board");
    let source = json!({"id":source_id,"title":"Fixture original","publisher":"integration test",
        "url":format!("https://example.invalid/{name}"),"retrieved_at":"2026-11-18","local_path":source_rel,"sha256":hash,
        "license":"test fixture","license_status":"verified"});
    let material = json!({"id":material_id,"name":"Oak test board","kind":"generic","entity_kind":"specimen",
        "category":"wood","source_id":source_id,"source_locator":"#/material"});
    let report = json!({"id":format!("{name}:value"),"property":raw_property,"material_id":material_id,"source_id":source_id,
        "source_locator":format!("#/properties/{raw_property}"),"unit":"kg CO2e","module":"A1","declared_unit":"kg",
        "value":value,"value_text":value.to_string(),"value_kind":"scalar","conditions":{"measured_mass_kg":1}});
    let missing = json!({"id":format!("{name}:missing"),"property":"thickness","material_id":material_id,"source_id":source_id,
        "source_locator":"#/properties/thickness","unit":"m","value":null,"value_text":"not reported","value_kind":"missing","data_status":"missing"});
    write(&folder.join("sources.jsonl"), &source);
    write(&folder.join("materials.jsonl"), &material);
    fs::write(
        folder.join("observations.jsonl"),
        format!("{report}\n{missing}\n"),
    )
    .unwrap();
    write(
        &folder.join("summary.json"),
        &json!({"dataset":name,"observations":2,"sources":1,"materials":1}),
    );
    format!("{source_id}#sha256:{hash}")
}

fn invoke(root: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ft-materials"))
        .current_dir(root)
        .arg("--root")
        .arg(root)
        .args(args)
        .output()
        .unwrap()
}
fn ok(root: &Path, args: &[&str]) -> Value {
    let out = invoke(root, args);
    assert!(
        out.status.success(),
        "ft-materials {args:?}: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap()
}
fn build(root: &Path, extra: &[&str]) -> Value {
    let mut args = vec![
        "build",
        "--require-originals",
        "--supplement",
        "north",
        "--supplement",
        "south",
    ];
    args.extend(extra);
    ok(root, &args)
}
fn base_files(store: &Path) -> Vec<PathBuf> {
    fs::read_dir(store)
        .unwrap()
        .map(|d| d.unwrap().path().join("materials.sqlite"))
        .filter(|p| p.is_file())
        .collect()
}

#[test]
fn reimport_reuses_foundation_and_retains_pinned_source_facts() {
    let temp = tempfile::tempdir().unwrap();
    let root = temp.path();
    foundation(root);
    let old_version = dataset(root, "north", 7, "gwp_total");
    let fixed_version = dataset(root, "south", 0, "global_warming_potential");
    let initial = build(root, &[]);
    let first = initial["snapshot"].as_str().unwrap();
    assert_eq!(
        initial["counts"],
        json!({"datasets":2,"sources":2,"materials":2,"observations":4})
    );
    let store = root.join("data/editions");
    let base = base_files(&store);
    assert_eq!(base.len(), 1);
    let metadata = fs::metadata(&base[0]).unwrap();
    let searched = ok(root, &["search", "eg", "--kind", "specimen"]);
    assert_eq!(searched["materials"].as_array().unwrap().len(), 2);
    let all = ok(
        root,
        &[
            "observations",
            "--property",
            "property:gwp_total",
            "--module",
            "A1",
        ],
    );
    let values = all["observations"].as_array().unwrap();
    assert_eq!(values.len(), 2);
    assert_eq!(values[0]["property"], "gwp_total");
    assert_eq!(values[1]["property"], "global_warming_potential");
    assert_eq!(values[0]["property_id"], values[1]["property_id"]);
    assert_eq!(values[0]["source_version_id"], old_version);
    assert_eq!(values[1]["source_version_id"], fixed_version);
    assert_eq!(values[1]["value"].as_f64(), Some(0.0));
    let checked = ok(root, &["lookup", "north:board"]);
    assert_eq!(checked["total"], 2);
    let absent = &checked["observations"][0];
    assert_eq!(absent["value_kind"], "missing");
    assert!(absent["value"].is_null());
    assert_eq!(absent["value_text"], "not reported");
    assert_eq!(absent["source_locator"], "#/properties/thickness");

    let new_version = dataset(root, "north", 9, "gwp_total");
    let inactive = build(root, &["--no-activate"]);
    let second = inactive["snapshot"].as_str().unwrap();
    assert_ne!(first, second);
    assert_eq!(ok(root, &["status"])["snapshot"], first);
    assert_eq!(build(root, &["--expect", second])["snapshot"], second);
    assert_eq!(inactive["base_sha256"], initial["base_sha256"]);
    assert_eq!(base_files(&store), base);
    assert_eq!(
        fs::metadata(&base[0]).unwrap().modified().unwrap(),
        metadata.modified().unwrap()
    );
    assert_ne!(new_version, old_version);
    let source = ok(root, &["--snapshot", first, "source", "north:source"]);
    assert_eq!(source["source"]["source_version_id"], old_version);
    let pinned = ok(
        root,
        &[
            "--snapshot",
            first,
            "lookup",
            "north:board",
            "--property",
            "property:gwp_total",
        ],
    );
    let current = ok(
        root,
        &["lookup", "north:board", "--property", "property:gwp_total"],
    );
    assert_eq!(pinned["observations"][0]["value"].as_f64(), Some(7.0));
    assert_eq!(current["observations"][0]["value"].as_f64(), Some(9.0));
    let diff = ok(root, &["changes", first, second]);
    assert_eq!(
        diff["sources"],
        json!([{"id":"north:source","before":old_version,"after":new_version}])
    );
    assert_eq!(ok(root, &["--snapshot", first, "verify"])["ok"], true);

    // A rejected replacement may neither change latest nor publish a partial edition.
    let old_pointer = fs::read(store.join("latest.json")).unwrap();
    fs::write(root.join("north/observations.jsonl"), "{truncated").unwrap();
    let failed = invoke(
        root,
        &[
            "build",
            "--require-originals",
            "--supplement",
            "north",
            "--supplement",
            "south",
        ],
    );
    assert!(!failed.status.success());
    assert!(
        String::from_utf8(failed.stderr)
            .unwrap()
            .contains("observations.jsonl")
    );
    assert_eq!(fs::read(store.join("latest.json")).unwrap(), old_pointer);
    assert_eq!(ok(root, &["status"])["snapshot"], second);
    let editions = fs::read_dir(&store)
        .unwrap()
        .filter_map(|p| p.ok())
        .filter(|p| p.file_name().to_string_lossy().starts_with("u2-"))
        .count();
    assert_eq!(editions, 2);
}
