use flate2::read::GzDecoder;
use serde_json::Value;
use std::{
    fs::{self, File},
    io::{BufRead, BufReader},
    path::{Path, PathBuf},
    process::Command,
};

fn supplement(root: &Path) -> PathBuf {
    root.join("data/supplements/field-sources")
}

#[test]
fn field_sources_rebuild_byte_for_byte_and_reject_damaged_originals() {
    let published = supplement(Path::new(env!("CARGO_MANIFEST_DIR")));
    let temp = tempfile::tempdir().unwrap();
    let folder = supplement(temp.path());
    fs::create_dir_all(folder.join("originals")).unwrap();
    for name in ["archive.json", "transcription.json"] {
        fs::copy(published.join(name), folder.join(name)).unwrap();
    }
    for file in fs::read_dir(published.join("originals")).unwrap() {
        let file = file.unwrap();
        fs::copy(file.path(), folder.join("originals").join(file.file_name())).unwrap();
    }
    let run = || {
        Command::new(env!("CARGO_BIN_EXE_ft-materials"))
            .arg("--root")
            .arg(temp.path())
            .arg("collect-field-sources")
            .output()
            .unwrap()
    };
    let rebuilt = run();
    assert!(
        rebuilt.status.success(),
        "{}",
        String::from_utf8_lossy(&rebuilt.stderr)
    );
    for name in [
        "sources.jsonl",
        "materials.jsonl.gz",
        "facts.jsonl.gz",
        "observations.jsonl.gz",
        "summary.json",
    ] {
        assert!(
            fs::read(published.join(name)).unwrap() == fs::read(folder.join(name)).unwrap(),
            "Non-reproducible output: {name}"
        );
    }
    let before = fs::read(folder.join("facts.jsonl.gz")).unwrap();
    fs::write(folder.join("originals/target1.csv"), "broken").unwrap();
    let rejected = run();
    assert!(!rejected.status.success());
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("checksum failed"));
    assert!(before == fs::read(folder.join("facts.jsonl.gz")).unwrap());
}

#[test]
fn evidence_preserves_table_conditions_units_and_curve_pairing() {
    let folder = supplement(Path::new(env!("CARGO_MANIFEST_DIR")));
    let input = BufReader::new(GzDecoder::new(
        File::open(folder.join("facts.jsonl.gz")).unwrap(),
    ));
    let first_alpha = BufReader::new(File::open(folder.join("originals/alpha1.csv")).unwrap())
        .lines()
        .next()
        .unwrap()
        .unwrap();
    let measured: Vec<f64> = first_alpha
        .trim_start_matches('\u{feff}')
        .split(", ")
        .map(|v| v.replace(',', ".").parse().unwrap())
        .collect();
    let mut covered = [false; 8];
    for l in input.lines() {
        let f: Value = serde_json::from_str(&l.unwrap()).unwrap();
        let c = &f["conditions"];
        match (
            f["material_id"].as_str().unwrap(),
            f["field_id"].as_str().unwrap(),
        ) {
            ("field-sources:material:acoustic-Green-1", "sound_absorption_coefficient")
                if c["measurement_row"] == 1 =>
            {
                let curve = &f["value"];
                assert_eq!(curve["x_values"][0], 250.0);
                assert_eq!(curve["x_values"][2560], 4250.0);
                let extracted: Vec<_> = curve["y_values"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|n| n.as_f64().unwrap())
                    .collect();
                assert_eq!(extracted, measured);
                assert_eq!(c["installation_configuration"], "T1");
                assert_eq!(c["relative_humidity_percent"], 40);
                covered[0] = true;
            }
            ("field-sources:material:nist-633a", "chemical_constituent")
                if c["constituent"] == "Hg" =>
            {
                assert_eq!(f["unit"], "ng/g");
                assert_eq!(f["value"], 24.70);
                assert_eq!(c["uncertainty"], 0.81);
                covered[1] = true;
            }
            ("field-sources:material:wood-flooring-1", "reaction_to_fire") => {
                assert_eq!(f["value"], "Cfl - s1");
                assert_eq!(c["minimum_overall_thickness_mm"], 8);
                assert!(c["footnotes"]["6"].as_str().unwrap().contains("A2"));
                covered[2] = true;
            }
            ("field-sources:material:cement", "price_quote") if c["year"] == 2024 => {
                assert_eq!(c["estimated"], true);
                assert_eq!(f["value"], 160);
                assert_eq!(f["unit"], "USD/t");
                covered[3] = true;
            }
            ("field-sources:material:recreate-BR_FI_STTO_KYTU_1982C_Pa-1305", "reuse_evidence") => {
                assert_eq!(f["value"]["Intervention Class"], "Installation-Ready");
                assert!(f["value"]["Building ID"].is_string());
                assert_eq!(f["source_locator"], "'Beam ID'!A2:P2");
                covered[4] = true;
            }
            ("field-sources:material:charring-1", "charring_rate")
                if c["exposure"] == "ASTM E119" =>
            {
                assert_eq!(f["value"], 1.24);
                assert_eq!(f["unit"], "min/mm");
                assert_eq!(c["char_temperature_criterion_degC"], 288);
                covered[5] = true;
            }
            ("field-sources:material:connector-1", "fastener_capacity")
                if c["wood_group"] == 1 && c["load_angle_to_grain_deg"] == 0 =>
            {
                assert_eq!(f["value"], 7940);
                assert_eq!(f["unit"], "N");
                assert_eq!(c["minimum_member_thickness_one_connector_mm"], 25);
                covered[6] = true;
            }
            ("field-sources:material:wood-flooring-5", "layer_sequence") => {
                assert_eq!(f["value"][1]["minimum_thickness"]["value"], 5);
                covered[7] = true;
            }
            _ => {}
        }
    }
    assert_eq!(covered, [true; 8]);
}
