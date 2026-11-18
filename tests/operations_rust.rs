//! Exercise the documented CLI, including reconstruction on a fresh, offline computer.
use serde_json::Value;
use std::{fs, path::Path, process::Command};

fn records(path: &Path) -> Vec<Value> {
    fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}

#[test]
fn archived_originals_reproduce_public_facts_and_reject_corruption() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let public = root.join("data/supplements/operations");
    let temp = tempfile::tempdir().unwrap();
    let dest = temp.path().join("data/supplements/operations");
    fs::create_dir_all(&dest).unwrap();
    fs::copy(
        public.join("oekobaudat-originals.zip"),
        dest.join("oekobaudat-originals.zip"),
    )
    .unwrap();
    // Licensed JSON originals travel with Git. The separately published IBU PDF
    // has a publisher download recipe, and is checked in the local-original run.
    let lock: Vec<Value> =
        serde_json::from_slice(&fs::read(public.join("public.lock.json")).unwrap()).unwrap();
    let licensed: Vec<&Value> = lock.iter().filter(|r| r.get("pointer").is_some()).collect();
    fs::write(
        dest.join("public.lock.json"),
        serde_json::to_vec(&licensed).unwrap(),
    )
    .unwrap();
    let run = || {
        Command::new(env!("CARGO_BIN_EXE_ft-materials"))
            .arg("--root")
            .arg(temp.path())
            .args(["collect-operations", "--offline"])
            .output()
            .unwrap()
    };
    let ok = run();
    assert!(
        ok.status.success(),
        "{}",
        String::from_utf8_lossy(&ok.stderr)
    );
    let expected: Vec<Value> = records(&public.join("facts.jsonl"))
        .into_iter()
        .filter(|v| {
            v["source_id"]
                .as_str()
                .unwrap()
                .starts_with("environmental:")
        })
        .collect();
    assert_eq!(expected, records(&dest.join("facts.jsonl")));
    let carpet: Vec<_> = expected
        .iter()
        .filter(|v| v["material_id"].as_str().unwrap().contains("7ee2591b"))
        .collect();
    assert!(
        carpet
            .iter()
            .any(|f| f["field_id"] == "maintenance_action" && f["value"] == "vacuum")
    );
    assert!(
        !carpet
            .iter()
            .any(|f| f["field_id"] == "maintenance_frequency")
    );
    let raw_path = temp
        .path()
        .join(licensed[0]["source"]["local_path"].as_str().unwrap());
    fs::write(raw_path, b"altered").unwrap();
    let rejected = run();
    assert!(!rejected.status.success());
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("checksum mismatch"));
    assert_eq!(expected, records(&dest.join("facts.jsonl")));
}

#[test]
fn product_performance_and_life_bounds_retain_scope() {
    let rows = records(
        &Path::new(env!("CARGO_MANIFEST_DIR")).join("data/supplements/operations/facts.jsonl"),
    );
    let product: Vec<_> = rows
        .iter()
        .filter(|v| v["material_id"].as_str().unwrap().contains("c54c16f6"))
        .collect();
    let life: Vec<_> = product
        .iter()
        .filter(|v| v["field_id"] == "service_life_value")
        .collect();
    assert_eq!(life.len(), 2);
    for inclusive in [true, false] {
        assert!(
            life.iter()
                .any(|f| f["value"]["lower_bound"] == 50
                    && f["value"]["lower_inclusive"] == inclusive)
        );
    }
    let fire = product
        .iter()
        .find(|f| f["field_id"] == "reaction_to_fire")
        .unwrap();
    assert_eq!(fire["value"]["class"], "A2-s1,d0");
    assert!(
        fire["conditions"]["component"]
            .as_str()
            .unwrap()
            .contains("acoustic tissue and mineral wool")
    );
    let svhc = product
        .iter()
        .find(|f| f["field_id"] == "chemical_constituent")
        .unwrap();
    assert_eq!(svhc["value"]["upper_bound"], 0.1);
    assert_eq!(svhc["value"]["upper_inclusive"], true);
}

#[test]
#[ignore = "requires the publisher PDFs from ft-materials collect-operations --danish"]
fn danish_source_pdfs_preserve_different_kinds_of_advice() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let temp = tempfile::tempdir().unwrap();
    let result = Command::new(env!("CARGO_BIN_EXE_ft-materials"))
        .current_dir(root)
        .args(["collect-operations", "--danish", "--offline", "--output"])
        .arg(temp.path())
        .output()
        .unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let rows = records(&temp.path().join("facts.jsonl"));
    assert_eq!(rows.len(), 109);
    let rv2: Vec<_> = rows
        .iter()
        .filter(|f| {
            f["material_id"] == "epd-danmark:record:9a0b48bb30ea8a2ac58c9a594232ead8"
                && f["field_id"] == "maintenance_frequency"
        })
        .collect();
    assert_eq!(rv2.len(), 2);
    assert!(rv2.iter().all(|f| f["value_status"] == "conflicting"));
    assert!(
        rv2.iter()
            .any(|f| f["value"] == 1 && f["unit"] == "times/year")
    );
    assert!(
        rv2.iter()
            .any(|f| f["value"] == 18 && f["unit"] == "months/interval")
    );
    let door: Vec<_> = rows
        .iter()
        .filter(|f| f["material_id"] == "epd-danmark:record:3746df4da119c92cf0998ed1eb0b3deb")
        .collect();
    assert!(
        door.iter()
            .any(|f| f["field_id"] == "service_life_value" && f["value"] == 30)
    );
    assert!(door.iter().any(|f| f["field_id"] == "condition_trigger"
        && f["conditions"]["basis"] == "manufacturer_maintenance_instruction"
        && f["conditions"]["component"] == "hinges"));
    assert!(
        door.iter()
            .any(|f| f["field_id"] == "resources_per_action" && f["value"]["amount"] == 0.94)
    );
}
