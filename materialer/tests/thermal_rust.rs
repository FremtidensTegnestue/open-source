#[path = "../src/thermal.rs"]
mod thermal;

use serde_json::Value;
use std::{fs, path::Path};

#[test]
fn reproduce_all_tampere_records_from_pinned_zip_and_workbook() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let reference = root.join("data/supplements/tampere");
    let temp = tempfile::tempdir().unwrap();
    let summary = thermal::run(thermal::Args {
        root: root.into(),
        output: Some(temp.path().into()),
    })
    .unwrap();
    assert_eq!(summary["observations"], 602);
    assert_eq!(summary["curve_points"], 3329);
    assert_eq!(summary["workbook_comparisons"]["identical"], 71);
    for name in [
        "sources.jsonl",
        "materials.jsonl",
        "observations.jsonl",
        "workbook-comparison.jsonl",
        "summary.json",
    ] {
        let expected = fs::read_to_string(reference.join(name)).unwrap();
        let actual = fs::read_to_string(temp.path().join(name)).unwrap();
        assert_eq!(actual.lines().count(), expected.lines().count(), "{name}");
        assert!(actual == expected, "{name} must be byte-reproducible");
        for (i, (a, b)) in actual.lines().zip(expected.lines()).enumerate() {
            assert_eq!(
                serde_json::from_str::<Value>(a).unwrap(),
                serde_json::from_str::<Value>(b).unwrap(),
                "{name} row {}",
                i + 1
            );
        }
    }
}

#[test]
fn corrupted_original_is_rejected_before_publication() {
    let temp = tempfile::tempdir().unwrap();
    let raw = temp.path().join("data/supplements/tampere/originals");
    fs::create_dir_all(&raw).unwrap();
    fs::write(raw.join("materialProperties.zip"), b"wrong").unwrap();
    let output = temp.path().join("out");
    assert!(
        thermal::run(thermal::Args {
            root: temp.path().into(),
            output: Some(output.clone())
        })
        .is_err()
    );
    assert!(!output.exists());
}

#[test]
fn compare_each_observation_with_the_independent_specimen_members() {
    use std::{collections::BTreeMap, io::Read};
    use zip::ZipArchive;

    let folder = Path::new(env!("CARGO_MANIFEST_DIR")).join("data/supplements/tampere");
    let mut zip =
        ZipArchive::new(fs::File::open(folder.join("originals/materialProperties.zip")).unwrap())
            .unwrap();
    let mut specimens = BTreeMap::new();
    for i in 0..zip.len() {
        let mut file = zip.by_index(i).unwrap();
        let name = file.name().unwrap();
        if name.ends_with(".json") && !name.ends_with("/allMaterialProperties.json") {
            let mut document = String::new();
            file.read_to_string(&mut document).unwrap();
            let specimen: Value = serde_json::from_str(
                &document.replace("\"thickness\": NaN,", "\"thickness\": null,"),
            )
            .unwrap();
            specimens.insert(specimen["id"].as_str().unwrap().to_owned(), specimen);
        }
    }
    assert_eq!(specimens.len(), 43);
    let observations = fs::read_to_string(folder.join("observations.jsonl")).unwrap();
    let mut checked = 0;
    for line in observations.lines() {
        let o: Value = serde_json::from_str(line).unwrap();
        let id = o["conditions"]["specimen_id"].as_str().unwrap();
        let key = o["property"].as_str().unwrap();
        let s = &specimens[id];
        assert_eq!(
            o["source_locator"],
            format!("materialProperties/allMaterialProperties.json#/{id}/{key}")
        );
        assert_eq!(o["unit"], s[format!("{key}_unit")]);
        match o["value_kind"].as_str().unwrap() {
            "missing" => {
                assert!(s[key].is_null());
                assert_eq!(o["value_text"], "NaN");
            }
            "curve" => {
                assert_eq!(o["structured_value"]["y_values"], s[key]);
                assert_eq!(
                    o["structured_value"]["x_values"],
                    s[format!("{key}_relative_humidity")]
                );
            }
            "scalar" => assert_eq!(o["value"], s[key]),
            kind => panic!("Unexpected source value kind {kind}"),
        }
        checked += 1;
    }
    assert_eq!(checked, 602);
}
