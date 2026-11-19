//! Regression for source years, uncertainty, source blanks and hierarchy of the Danish tables.
use flate2::read::GzDecoder;
use serde_json::Value;
use std::{
    fs,
    io::{BufRead, BufReader},
    path::Path,
    process::Command,
};

fn cli(root: &Path, args: &[&str]) -> Value {
    let out = Command::new(env!("CARGO_BIN_EXE_ft-materials"))
        .arg("--root")
        .arg(root)
        .args(args)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap()
}
#[test]
fn source_scenario_columns_stay_distinct() {
    let tmp = tempfile::tempdir().unwrap();
    let root = tmp.path();
    let path = "data/supplements/ens-varme/originals/april-2026.xlsx";
    fs::create_dir_all(root.join(path).parent().unwrap()).unwrap();
    fs::copy(
        Path::new(env!("CARGO_MANIFEST_DIR")).join(path),
        root.join(path),
    )
    .unwrap();
    let stats = cli(root, &["collect-heating"]);
    assert_eq!(stats["materials"], 45);
    assert_eq!(stats["numeric_estimates"], 7449);
    let source =
        fs::File::open(root.join("data/supplements/ens-varme/observations.jsonl.gz")).unwrap();
    let mut lives = Vec::new();
    let mut missing = 0;
    for l in BufReader::new(GzDecoder::new(source)).lines() {
        let v: Value = serde_json::from_str(&l.unwrap()).unwrap();
        if v["value"].is_null() {
            assert_eq!(v["value_kind"], "missing");
            missing += 1;
        }
        if v["property"] == "technoeconomic_lifetime"
            && v["conditions"]["worksheet"] == "207 HP air-water,ex single"
            && v["conditions"]["projection_year"] == 2025
        {
            lives.push((
                v["conditions"]["estimate_kind"]
                    .as_str()
                    .unwrap()
                    .to_owned(),
                v["value"].as_f64().unwrap(),
            ));
        }
    }
    assert_eq!(missing, 2766);
    assert_eq!(
        lives,
        vec![
            ("ctrl".to_owned(), 20.),
            ("lower".to_owned(), 14.),
            ("upper".to_owned(), 25.)
        ]
    );
}
#[test]
fn publisher_lifetime_table_when_locally_archived() {
    let path = "data/raw/build-levetid/2021.xlsx";
    let origin = Path::new(env!("CARGO_MANIFEST_DIR")).join(path);
    if !origin.is_file() {
        return;
    }
    let tmp = tempfile::tempdir().unwrap();
    let root = tmp.path();
    fs::create_dir_all(root.join(path).parent().unwrap()).unwrap();
    fs::copy(origin, root.join(path)).unwrap();
    let stats = cli(root, &["collect-lifetimes", "--offline"]);
    assert_eq!(stats["numeric_lifetimes"], 1477);
    assert_eq!(stats["not_applicable"], 3);
    let facts = fs::read_to_string(root.join("data/staging/build-levetid/facts.jsonl")).unwrap();
    let group: Value = facts
        .lines()
        .map(|s| serde_json::from_str::<Value>(s).unwrap())
        .find(|v| v["id"] == "build-levetid:2021:l4:T8:years")
        .unwrap();
    assert_eq!(group["conditions"]["subject"], "Fundamenter, bygning");
    assert_eq!(group["value"].as_f64(), Some(100.));
}
