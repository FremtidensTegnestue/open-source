//! Rebuild a SolidCraft-to-BIMCraft specimen and verify both native assess paths.
use anyhow::{Context, Result, ensure};
use calamine::{DataType, Reader, Xlsx};
use clap::Parser;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::Cursor,
    path::{Path, PathBuf},
    process::Command,
};

#[derive(Parser)]
struct Args {
    #[arg(long, default_value = ".")]
    root: PathBuf,
    #[arg(long)]
    store: Option<PathBuf>,
    #[arg(long)]
    binary: Option<PathBuf>,
    #[arg(long)]
    before: Option<String>,
    #[arg(long)]
    after: Option<String>,
    #[arg(long, default_value = "output/unified-native")]
    output: PathBuf,
}
fn read(p: &Path) -> Result<Value> {
    Ok(serde_json::from_slice(&fs::read(p)?)?)
}
fn save(p: &Path, v: &Value) -> Result<()> {
    fs::create_dir_all(p.parent().context("Missing parent directory")?)?;
    let mut data = serde_json::to_vec_pretty(v)?;
    data.push(b'\n');
    fs::write(p, data)?;
    Ok(())
}
fn hash(b: &[u8]) -> String {
    hex::encode(Sha256::digest(b))
}
fn path(p: &Path) -> Result<String> {
    Ok(p.to_str().context("Non-UTF8 path")?.into())
}
fn run(cmd: &Path, args: &[String], code: i32) -> Result<String> {
    let r = Command::new(cmd)
        .args(args)
        .output()
        .with_context(|| cmd.display().to_string())?;
    ensure!(
        r.status.code() == Some(code),
        "{} {:?} exited {}: {} {}",
        cmd.display(),
        args,
        r.status,
        String::from_utf8_lossy(&r.stderr),
        String::from_utf8_lossy(&r.stdout)
    );
    Ok(String::from_utf8(r.stdout)?)
}
fn bim(
    model: Option<&Path>,
    commands: &[(&str, Value)],
    output: Option<&Path>,
) -> Result<Vec<Value>> {
    let mut args = vec!["run".into()];
    if let Some(p) = model {
        args.push(path(p)?);
    }
    for (cmd, v) in commands {
        args.extend(["--cmd".into(), format!("{cmd} {v}")]);
    }
    if let Some(p) = output {
        args.extend(["--save".into(), path(p)?]);
    }
    let mut docs = Vec::new();
    for l in run(Path::new("bimcraft-cli"), &args, 0)?
        .lines()
        .filter(|l| !l.is_empty())
    {
        let v: Value = serde_json::from_str(l)?;
        ensure!(v["error"].is_null() && v["ok"] != false, "BIMCraft: {v}");
        docs.push(v);
    }
    Ok(docs)
}
fn product_models(dir: &Path, selection: &Value, density: f64) -> Result<()> {
    let label = &selection["materials"]["lincrete"]["model_material_name"];
    let base = json!([
        {"command":"parameters.add","params":{"name":"thickness","expression":"20 mm"}},
        {"command":"solid.box","params":{"body_name":"FacadePanel","length":1000,"width":500,"height":"thickness"}},
        {"command":"material.create","params":{"name":label,"density_g_cm3":density/1000.,"color":"#b7b6ad"}},
        {"command":"material.assign","params":{"bodies":["FacadePanel"],"material":label}}
    ]);
    let rev =
        json!([{"command":"parameters.change","params":{"name":"thickness","expression":"24 mm"}}]);
    let split = json!([{"command":"solid.split_body","params":{"body":"FacadePanel","plane":{"origin":[500,0,0],"normal":[1,0,0]}}}]);
    for (name, previous, commands) in [
        ("base", None, base),
        ("revised", Some("base"), rev),
        ("split", Some("revised"), split),
    ] {
        let dest = dir.join(name);
        let script = dest.join("commands.json");
        save(&script, &json!({"commands":commands}))?;
        let sc = dest.join("model.sc");
        let glb = dest.join("transfer.glb");
        let project = dest.join("model.bimc");
        let mut args = vec![
            "run".into(),
            path(&script)?,
            "--param-check".into(),
            "strict".into(),
        ];
        if let Some(prev) = previous {
            args.extend(["--in".into(), path(&dir.join(prev).join("model.sc"))?]);
        }
        args.extend(["--save".into(), path(&sc)?, "--out".into(), path(&glb)?]);
        run(Path::new("solidcraft-cli"), &args, 0)?;
        let blank = dest.join("import.bimc");
        let replies = bim(
            None,
            &[
                ("new", json!({"name":format!("LinCrete-{name}")})),
                ("import_mesh", json!({"path":glb})),
                ("elements", json!({"category":"component"})),
            ],
            Some(&blank),
        )?;
        let import = replies
            .iter()
            .find(|v| v.get("left_out").is_some())
            .context("Missing import summary")?;
        ensure!(
            import["left_out"].as_object().is_some_and(|a| a.is_empty()),
            "BIM dropped geometry: {import}"
        );
        let elements = replies
            .iter()
            .find_map(|r| r["elements"].as_array())
            .context("Missing imported elements")?;
        ensure!(
            elements.len() == if name == "split" { 2 } else { 1 },
            "Wrong number of imported solids"
        );
        let mut assign = vec![("material", json!({"name":label}))];
        let mut parts = vec![];
        for e in elements {
            let name = e["family"].as_str().context("Missing family")?;
            let defs = bim(Some(&blank), &[("family", json!({"name":name}))], None)?;
            let forms = defs
                .iter()
                .find_map(|r| r["family"]["forms"].as_array())
                .context("Missing mesh form")?;
            ensure!(forms.len() == 1, "Expected one form per component");
            assign.push((
                "family",
                json!({"name":name,"form":{"id":forms[0]["id"],"material":label}}),
            ));
            parts.push(json!({"source_body":name,"bim_element_id":e["id"],"bim_guid":e["guid"]}));
        }
        bim(Some(&blank), &assign, Some(&project))?;
        save(
            &dest.join("transfer.json"),
            &json!({"schema_version":1,"cad_model_sha256":hash(&fs::read(sc)?),
             "glb_sha256":hash(&fs::read(glb)?),"bim_model_sha256":hash(&fs::read(project)?),"parts":parts}),
        )?;
    }
    Ok(())
}
fn original(root: &Path, relative: &str, url: &str, sha: &str) -> Result<Vec<u8>> {
    let file = root.join(relative);
    let cached = file.is_file();
    let data = if cached {
        fs::read(&file)?
    } else {
        reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs(90))
            .build()?
            .get(url)
            .send()?
            .error_for_status()?
            .bytes()?
            .to_vec()
    };
    ensure!(
        hash(&data) == sha,
        "Original source differs from {sha}: {url}"
    );
    if !cached {
        use std::io::Write;
        let parent = file.parent().context("Missing source directory")?;
        fs::create_dir_all(parent)?;
        let mut temp = tempfile::NamedTempFile::new_in(parent)?;
        temp.write_all(&data)?;
        if let Err(e) = temp.persist_noclobber(&file) {
            ensure!(
                e.error.kind() == std::io::ErrorKind::AlreadyExists
                    && hash(&fs::read(&file)?) == sha,
                "Could not preserve original {}",
                file.display()
            );
        }
    }
    Ok(data)
}
struct References {
    density: f64,
    factor: f64,
    br: [(f64, f64); 2],
}
fn refs(root: &Path) -> Result<References> {
    let data = original(
        root,
        "data/raw/environmental/oekobaudat/processes/c54c16f6-4295-4749-bff0-ba7ed4bc9117_00.01.000.json",
        "https://oekobaudat.de/OEKOBAU.DAT/resource/processes/c54c16f6-4295-4749-bff0-ba7ed4bc9117?format=json&view=extended&version=00.01.000",
        "dc2c7f72e2baa20ce500c307c447b0a94085fc7fcf499c9279fcb40bd7d80239",
    )?;
    let doc: Value = serde_json::from_slice(&data)?;
    let flow = &doc["exchanges"]["exchange"][0];
    let d = &flow["materialProperties"][0];
    let mass = flow["flowProperties"]
        .as_array()
        .and_then(|s| s.iter().find(|p| p["referenceFlowProperty"] == true))
        .context("Missing declared mass")?;
    ensure!(
        d["name"] == "gross density"
            && d["unit"] == "kg/m^3"
            && mass["referenceUnit"] == "kg"
            && flow["referenceFlow"] == true,
        "Unexpected declared density/basis"
    );
    let indicator = &doc["LCIAResults"]["LCIAResult"][0];
    let value = &indicator["other"]["anies"][1];
    ensure!(
        value["module"] == "A1-A3"
            && indicator["referenceToLCIAMethodDataSet"]["refObjectId"]
                == "6a37f984-a4b3-458a-a20a-64418c145fa2",
        "Wrong indicator/module"
    );
    let density = d["value"]
        .as_str()
        .context("Missing declared density")?
        .parse()?;
    let factor = value["value"]
        .as_str()
        .context("Missing factor")?
        .parse::<f64>()?
        / mass["meanValue"]
            .as_f64()
            .context("Missing declared amount")?;
    let bytes = original(
        root,
        "data/raw/br18/table-7-2025.xlsx",
        "https://www.bygningsreglementet.dk/media/1o1nnozd/tabel-7-2025.xlsx",
        "3ac0babdd803cc688e058c9b1096c9871c849362014d4da80564000b73bcdb18",
    )?;
    let mut wb = Xlsx::new(Cursor::new(bytes))?;
    let sheet = wb.worksheet_range("Sheet1")?;
    let mut br = [(0., 0.); 2];
    for (i, row) in [24, 128].into_iter().enumerate() {
        let value = |col| {
            sheet
                .get_value((row, col))
                .and_then(DataType::as_f64)
                .context("Missing BR18 cell")
        };
        br[i] = (value(10)?, value(4)?);
    }
    Ok(References {
        density,
        factor,
        br,
    })
}
fn near(a: &Value, want: f64) -> Result<()> {
    let n = a.as_f64().context("Missing measured quantity")?;
    ensure!(
        (want - n).abs() <= 1e-9f64.max(want.abs() * 2e-6),
        "{n} differs from {want}"
    );
    Ok(())
}
struct Check {
    bin: PathBuf,
    root: PathBuf,
    store: PathBuf,
    out: PathBuf,
}
impl Check {
    fn cli(&self, args: &[String], code: i32) -> Result<Value> {
        let mut base = vec![
            "--root".into(),
            path(&self.root)?,
            "--store".into(),
            path(&self.store)?,
        ];
        base.extend_from_slice(args);
        Ok(serde_json::from_str(&run(&self.bin, &base, code)?)?)
    }
    fn pair(
        &self,
        dir: &Path,
        pin: &Path,
        transfer: &Path,
        name: &str,
        expected: &Value,
        issue: Option<&str>,
    ) -> Result<Value> {
        let snapshot = read(pin)?["snapshot"].clone();
        let mut reports = json!({});
        let mut references = None;
        for (program, ext) in [("solidcraft", "sc"), ("bimcraft", "bimc")] {
            let mut cmd = vec![
                "assess".into(),
                path(&dir.join(format!("model.{ext}")))?,
                "--software".into(),
                program.into(),
                "--selection".into(),
                path(pin)?,
                "--transfer".into(),
                path(transfer)?,
            ];
            if program == "bimcraft" {
                cmd.push("--mesh-quantities".into());
            }
            let r = self.cli(&cmd, if issue.is_none() { 0 } else { 2 })?;
            save(
                &self
                    .out
                    .join("reports")
                    .join(name)
                    .join(format!("{program}.json")),
                &r,
            )?;
            ensure!(r["snapshot"] == snapshot, "Mismatched data edition");
            if let Some(old) = references.as_ref() {
                ensure!(
                    *old == r["selected_observations"],
                    "Selected observations differ between programs"
                );
            }
            references = Some(r["selected_observations"].clone());
            if let Some(code) = issue {
                ensure!(
                    r["status"] == "partial"
                        && r["warnings"]
                            .as_array()
                            .is_some_and(|ws| ws.iter().any(|w| w["code"] == code)),
                    "Missing diagnosis: {code}"
                );
                ensure!(
                    r["elements"]
                        .as_array()
                        .is_some_and(|es| !es.is_empty()
                            && es.iter().all(|e| e["calculations"] == json!({}))),
                    "A stale or split component retained results"
                );
                reports[program] = json!({"status":"partial","diagnosis":code});
                continue;
            }
            ensure!(r["status"] == "ok", "Assessment incomplete");
            let mut rows = json!({});
            for e in r["elements"].as_array().context("Missing results")? {
                let part = e["model_quantity_source"]
                    .get(if program == "solidcraft" {
                        "body_name"
                    } else {
                        "family_name"
                    })
                    .and_then(Value::as_str)
                    .context("Missing part ID")?;
                let exp = &expected[part];
                let m = &e["calculations"]["mass"];
                let c = &e["calculations"]["climate"][0];
                near(
                    &m["inputs"]["volume"]["value"],
                    exp[0].as_f64().context("Missing expected volume")?,
                )?;
                near(&m["value"], exp[1].as_f64().unwrap())?;
                near(&c["value"], exp[2].as_f64().unwrap())?;
                ensure!(c["module"] == "A1-A3", "Unexpected climate module");
                for v in [&m["inputs"]["density"], &c["inputs"]["source_observation"]] {
                    ensure!(
                        v["source_version_id"].is_string()
                            && v["source_url"].is_string()
                            && v["source_locator"].is_string(),
                        "Missing original source"
                    );
                }
                rows[part] = json!({"volume_m3":m["inputs"]["volume"]["value"],"mass_kg":m["value"],"gwp_A1_A3_kg_CO2e":c["value"]});
            }
            ensure!(
                rows.as_object().unwrap().len() == expected.as_object().unwrap().len(),
                "Part inventory differs"
            );
            reports[program] = rows;
        }
        Ok(reports)
    }
}
fn main() -> Result<()> {
    let args = Args::parse();
    let root = args.root.canonicalize()?;
    let example = root.join("examples/unified-workflow");
    let fixture = root.join("examples/integrated-workflow");
    let store = args.store.unwrap_or_else(|| root.join("data/editions"));
    let exe = std::env::current_exe()?;
    let bin = args.binary.unwrap_or_else(|| {
        exe.parent()
            .unwrap()
            .parent()
            .unwrap()
            .join(format!("ft-materials{}", std::env::consts::EXE_SUFFIX))
    });
    let out = std::path::absolute(args.output)?;
    fs::create_dir_all(&out)?;
    ensure!(
        fs::read_dir(&out)?.next().is_none(),
        "Provide an empty output directory"
    );
    let check = Check {
        root: root.clone(),
        store,
        bin,
        out: out.clone(),
    };
    let mut selection = read(&example.join("selection.json"))?;
    let before = args
        .before
        .unwrap_or_else(|| selection["snapshot"].as_str().unwrap_or("").to_owned());
    let after = if let Some(id) = args.after {
        id
    } else {
        check.cli(&["status".into()], 0)?["snapshot"]
            .as_str()
            .context("Latest snapshot missing")?
            .into()
    };
    ensure!(
        before != after && before != "latest" && after != "latest",
        "Supply two distinct immutable edition IDs"
    );
    let References {
        density,
        factor,
        br,
    } = refs(&root)?;
    let models = out.join("models");
    selection["snapshot"] = json!(before);
    let pin = out.join("selection.json");
    save(&pin, &selection)?;
    let mut summary = json!({"status":"running","implementation":"Rust","snapshots":[before,after],
        "programs":{"solidcraft":run(Path::new("solidcraft-cli"),&["--version".into()],0)?.trim(),"bimcraft":run(Path::new("bimcraft-cli"),&["--version".into()],0)?.trim()}});
    save(&out.join("verification.json"), &summary)?;
    product_models(&models, &selection, density)?;
    let mut expected = json!({});
    for (rev, thickness) in [("base", 0.020), ("revised", 0.024)] {
        let volume = 0.5 * thickness;
        let kg = volume * density;
        expected = json!({"FacadePanel":[volume,kg,kg*factor]});
        let model = models.join(rev);
        summary["product"][rev] = check.pair(
            &model,
            &pin,
            &model.join("transfer.json"),
            rev,
            &expected,
            None,
        )?;
    }
    let revised = models.join("revised");
    let transfer = revised.join("transfer.json");
    let next = out.join("after-selection.json");
    selection["snapshot"] = json!(after);
    save(&next, &selection)?;
    for (name, sel) in [("after", next.as_path()), ("replay", pin.as_path())] {
        let value = check.pair(&revised, sel, &transfer, name, &expected, None)?;
        ensure!(
            value == summary["product"]["revised"],
            "Originally selected source or geometry changed"
        );
        let a = read(&out.join("reports/revised/solidcraft.json"))?;
        let b = read(&out.join("reports").join(name).join("solidcraft.json"))?;
        ensure!(
            a["selected_observations"] == b["selected_observations"],
            "Pinned source differs"
        );
    }
    summary["replay"] = json!("identical");
    summary["stale_map"] = check.pair(
        &revised,
        &pin,
        &models.join("base/transfer.json"),
        "stale",
        &Value::Null,
        Some("model_changed"),
    )?;
    let split = models.join("split");
    summary["split"] = check.pair(
        &split,
        &pin,
        &split.join("transfer.json"),
        "split",
        &Value::Null,
        Some("part_inventory_changed"),
    )?;
    let manifest = read(&fixture.join("material-manifest.json"))?;
    let mut sel = json!({"schema_version":1,"snapshot":before,"parts":manifest["source_body_to_material"],"materials":{}});
    for (key, m) in manifest["material_records"].as_object().unwrap() {
        let mid = m["id"].as_str().unwrap();
        sel["materials"][key] = json!({"material_id":mid,"model_material_name":m["name"],"selection_note":manifest["scope"],
            "density_observation_id":format!("{mid}:mass"),"gwp_observation_ids":[format!("{mid}:gwp:A1-A3")],"operations":["mass","climate"]});
    }
    let fpin = out.join("fixture-selection.json");
    save(&fpin, &sel)?;
    for (rev, t) in [("base", 0.100), ("revised", 0.120)] {
        let v = (1.5 - 0.3 * 0.2) * t;
        let s = 0.0008;
        let steel = json!([s, s * br[1].0, s * br[1].0 / 1000. * br[1].1]);
        let expected =
            json!({"ConcretePanel":[v,v*br[0].0,v*br[0].1],"Rail_A":steel,"Rail_B":steel});
        let dir = fixture.join(rev);
        summary["three_parts"][rev] = check.pair(
            &dir,
            &fpin,
            &dir.join("transfer-material-map.json"),
            &format!("fixture-{rev}"),
            &expected,
            None,
        )?;
    }
    for report in ["revised", "fixture-revised"] {
        let assessment = read(&out.join("reports").join(report).join("solidcraft.json"))?;
        for (id, observation) in assessment["selected_observations"]
            .as_object()
            .context("Missing provenance")?
        {
            summary["observations"][id] = observation.clone();
        }
    }
    summary["status"] = json!("passed");
    save(&out.join("verification.json"), &summary)?;
    println!("{}", out.join("verification.json").display());
    Ok(())
}
