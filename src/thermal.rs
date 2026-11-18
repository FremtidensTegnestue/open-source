//! Import the primary Tampere specimen JSON, keeping complete humidity curves and XLSX evidence.
use anyhow::{Context, Result, ensure};
use calamine::{Data, DataType, Range, Reader, Xlsx};
use clap::Args as ClapArgs;
use serde_json::{Map, Value, json, value::RawValue};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    io::{Cursor, Read, Write},
    path::{Path, PathBuf},
    time::Duration,
};
use tempfile::NamedTempFile;
use zip::ZipArchive;

#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Repository containing data/supplements/tampere/originals.
    #[arg(skip)]
    pub root: PathBuf,
    /// Normalized bundle destination. Defaults to data/supplements/tampere under --root.
    #[arg(long)]
    pub output: Option<PathBuf>,
}

const SUBDIR: &str = "data/supplements/tampere";
const MEMBER: &str = "materialProperties/allMaterialProperties.json";
const BOOK: &str = "materialProperties/materialProperies.xlsx";
const DOI: &str = "10.5281/zenodo.17778563";
const ATTRIBUTION: &str = "Antti Mikkonen and Juha Vinha, Tampere University Building Physics, Finland (2025). Dataset of hygrothermal measurements of 56 timber-framed wall structures and material properties. Version 1.0.0. https://doi.org/10.5281/zenodo.17778563";
const SID: &str = "tampere:source:17778563:materialProperties.zip";
const FILES: [(&str, &str, &str, &str); 2] = [
    (
        "materialProperties.zip",
        "58c5cc9296202304021efef1d3f302b38fe7c40d183602c1b7c4cd7a1de7ffe3",
        "2026-11-18T14:37:53Z",
        "application/zip",
    ),
    (
        "README.md",
        "8b73158e2bf68a94a0e56f993f0f45cc68bc6749745d334e23b84405ce7e3fc6",
        "2026-11-18T14:37:52Z",
        "text/markdown",
    ),
];
const FIELDS: [&str; 14] = [
    "density",
    "thickness",
    "water_capillary_absorption_coefficient",
    "specific_heat_capacity",
    "porosity",
    "sorption_moisture_content",
    "adsorption_moisture_content",
    "desorption_moisture_content",
    "moisture_diffusivity",
    "moisture_diffusivity_adsorption",
    "thermal_conductivity",
    "water_vapour_diffusion_resistance_factor",
    "water_vapour_permeability_with_respect_to_humidity_by_volume",
    "water_vapour_permeability_with_respect_to_partial_water_vapour_pressure",
];
const IDENTITIES: [&str; 9] = [
    "category",
    "material_type",
    "product_name",
    "manufacturer",
    "id",
    "source",
    "note",
    "lisence",
    "original_source",
];

fn original(
    root: &Path,
    name: &str,
    hash: &str,
    timestamp: &str,
    media: &str,
) -> Result<(Value, Vec<u8>)> {
    let rel = format!("{SUBDIR}/originals/{name}");
    let path = root.join(&rel);
    let url = format!("https://zenodo.org/api/records/17778563/files/{name}/content");
    let data = match fs::read(&path) {
        Ok(data) => data,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            let data = reqwest::blocking::Client::builder()
                .timeout(Duration::from_secs(90))
                .build()?
                .get(&url)
                .send()?
                .error_for_status()?
                .bytes()?
                .to_vec();
            ensure!(
                hex::encode(Sha256::digest(&data)) == hash,
                "Publisher returned different bytes for {name}"
            );
            let parent = path.parent().context("Missing originals directory")?;
            fs::create_dir_all(parent)?;
            let mut temp = NamedTempFile::new_in(parent)?;
            temp.write_all(&data)?;
            match temp.persist_noclobber(&path) {
                Ok(_) => {}
                Err(e) if e.error.kind() == std::io::ErrorKind::AlreadyExists => {
                    ensure!(
                        fs::read(&path)? == data,
                        "Another file already exists at {}",
                        path.display()
                    );
                }
                Err(e) => return Err(e.into()),
            }
            data
        }
        Err(e) => return Err(e.into()),
    };
    ensure!(
        hex::encode(Sha256::digest(&data)) == hash,
        "Checksum mismatch for {}",
        path.display()
    );
    Ok((
        json!({
            "id":format!("tampere:source:17778563:{name}"),"title":format!("Tampere hygrothermal dataset, {name}"),
            "publisher":"Tampere University Building Physics / Zenodo","url":url,"doi":DOI,"source_version":"1.0.0",
            "retrieved_at":timestamp,"local_path":rel,"sha256":hash,"media_type":media,"license":"CC BY 4.0",
            "license_url":"https://creativecommons.org/licenses/by/4.0/","license_status":"verified","attribution":ATTRIBUTION,
            "modifications":"Unmodified original. Structured records use the primary JSON from the ZIP."
        }),
        data,
    ))
}

type Specimen = BTreeMap<String, Box<RawValue>>;

fn parse_specimens(text: &str) -> Result<BTreeMap<String, Specimen>> {
    // The pinned release serializes exactly 19 absent thicknesses as bare NaN.
    // Match only the thickness member in that encoding and preserve the source marker below.
    ensure!(
        text.matches("\"thickness\": NaN,").count() == 19,
        "Unexpected missing-value encoding or edition"
    );
    Ok(serde_json::from_str(
        &text.replace("\"thickness\": NaN,", "\"thickness\": null,"),
    )?)
}

fn property(row: &Specimen, name: &str) -> Result<Value> {
    Ok(serde_json::from_str(
        row.get(name)
            .with_context(|| format!("Missing field {name}"))?
            .get(),
    )?)
}

fn string(row: &Specimen, name: &str) -> Result<String> {
    serde_json::from_str(
        row.get(name)
            .with_context(|| format!("Missing text field {name}"))?
            .get(),
    )
    .map_err(Into::into)
}

fn material(id: &str, row: &Specimen) -> Result<Value> {
    ensure!(
        string(row, "id")? == id && string(row, "source")? == DOI,
        "Unexpected specimen identity {id}"
    );
    let source_fields: Map<String, Value> = IDENTITIES
        .iter()
        .map(|s| Ok((s.to_string(), property(row, s)?)))
        .collect::<Result<_>>()?;
    let name = string(row, "product_name")?;
    Ok(json!({
        "id":format!("tampere:material:{id}"),"name":name,"kind":"product","entity_kind":"specimen",
        "category":source_fields["category"],"description":source_fields["original_source"],"source_id":SID,
        "source_locator":format!("{MEMBER}#/{id}"),"source_fields":source_fields,
        "aliases":[string(row,"material_type")?.replace('_'," "),format!("{} {}",string(row,"manufacturer")?,name)]
    }))
}

fn numeric_array(v: &Value) -> Result<Vec<f64>> {
    v.as_array()
        .context("Missing numeric array")?
        .iter()
        .map(|n| {
            n.as_f64()
                .filter(|f| f.is_finite())
                .context("Expected finite number")
        })
        .collect()
}

fn observation(id: &str, row: &Specimen, key: &str) -> Result<Value> {
    let base = format!("{MEMBER}#/{id}");
    let value = property(row, key)?;
    let unit = string(row, &format!("{key}_unit"))?;
    let text: String = row[key]
        .get()
        .chars()
        .filter(|c| !c.is_ascii_whitespace())
        .collect();
    let mut obs = json!({
        "id":format!("tampere:observation:{id}:{key}"),"material_id":format!("tampere:material:{id}"),
        "property":key,"source_id":SID,"source_locator":format!("{base}/{key}"),"unit":unit,"data_status":"reported",
        "method":"Published material properties from the Tampere building physics study",
        "conditions":{"specimen_id":id,"research_project":property(row,"original_source")?},
        "value":null,"value_text":text,
    });
    if value.is_null() {
        ensure!(key == "thickness", "Unexpected null at {base}/{key}");
        obs["value_text"] = json!("NaN");
        obs["data_status"] = json!("missing");
        obs["value_kind"] = json!("missing");
    } else if value.is_array() {
        let axis = format!("{key}_relative_humidity");
        let xs = property(row, &axis)?;
        let ys = numeric_array(&value)?;
        let humidity = numeric_array(&xs)?;
        ensure!(
            !ys.is_empty()
                && humidity.len() == ys.len()
                && humidity.iter().all(|x| (0.0..=1.0).contains(x))
                && humidity.windows(2).all(|w| w[0] < w[1]),
            "Invalid paired curve {id}/{key}"
        );
        obs["value_kind"] = json!("curve");
        obs["structured_value"] = json!({"x_property":"relative_humidity","x_unit":string(row,&format!("{axis}_unit"))?,
            "x_values":xs,"x_source_locator":format!("{base}/{axis}"),"y_unit":unit,"y_values":value});
    } else {
        ensure!(value.is_number(), "Unexpected scalar type {id}/{key}");
        obs["value_kind"] = json!("scalar");
        obs["value"] = value;
    }
    Ok(obs)
}

struct Reconciliation {
    sheet: &'static str,
    start: u32,
    end: u32,
    marker: &'static str,
    unit: &'static str,
    condition: Value,
}

fn field(key: &str) -> Option<Reconciliation> {
    let (sheet, start, end, marker, unit, condition) = match key {
        "density" => (
            "Table1",
            4,
            4,
            "DRY",
            "kg/m^3",
            json!({"moisture_condition":"dry"}),
        ),
        "sorption_moisture_content" => (
            "Table1",
            7,
            17,
            "+23°C",
            "kg/(m^3)",
            json!({"temperature_c":23}),
        ),
        "adsorption_moisture_content" => (
            "Table1",
            18,
            24,
            "+23°C",
            "kg/(m^3)",
            json!({"temperature_c":23}),
        ),
        "desorption_moisture_content" => (
            "Table1",
            25,
            31,
            "+23°C",
            "kg/(m^3)",
            json!({"temperature_c":23}),
        ),
        "water_vapour_diffusion_resistance_factor" => {
            ("Table2", 4, 12, "+23°C", "-", json!({"temperature_c":23}))
        }
        "thermal_conductivity" => (
            "Table2",
            20,
            25,
            "+10°C",
            "W/(mK)",
            json!({"temperature_c":10}),
        ),
        _ => return None,
    };
    Some(Reconciliation {
        sheet,
        start,
        end,
        marker,
        unit,
        condition,
    })
}
fn column(mut pos: u32) -> String {
    let mut letters = Vec::new();
    while pos > 0 {
        pos -= 1;
        letters.push((b'A' + (pos % 26) as u8) as char);
        pos /= 26;
    }
    letters.into_iter().rev().collect()
}

fn reconcile(obs: &mut Value, spec: &Reconciliation, sheet: &Range<Data>) -> Result<Value> {
    let cell = |r: u32, c: u32| sheet.get_value((r - 1, c - 1));
    let id = obs["conditions"]["specimen_id"]
        .as_str()
        .context("Missing specimen ID")?;
    let mut audit = json!({"observation_id":obs["id"],"primary_locator":obs["source_locator"]});
    let height = sheet.end().context("Empty worksheet")?.0 + 1;
    let Some(row) = (6..=height).find(|r| cell(*r, 2).is_some_and(|v| v.get_string() == Some(id)))
    else {
        audit["status"] = json!("specimen_absent_from_sheet");
        return Ok(audit);
    };
    let first = column(spec.start);
    let last = column(spec.end);
    let prefix = format!("{BOOK}#{}!", spec.sheet);
    let mut pointers = json!({"header":format!("{prefix}{first}4"),"specimen_id":format!("{prefix}B{row}"),
        "values":format!("{prefix}{first}{row}:{last}{row}")});
    audit
        .as_object_mut()
        .unwrap()
        .extend(pointers.as_object().unwrap().clone());
    ensure!(
        cell(4, spec.start).is_some_and(|c| c.to_string().contains(spec.marker))
            && obs["unit"] == spec.unit,
        "Unexpected workbook header at {prefix}{first}4"
    );
    let ys: Option<Vec<f64>> = (spec.start..=spec.end)
        .map(|c| cell(row, c)?.to_string().parse::<f64>().ok())
        .collect();
    let Some(ys) = ys else {
        audit["status"] = json!("missing_or_non_numeric_workbook_value");
        return Ok(audit);
    };
    let mut axes = None;
    let same = if obs["value_kind"] == "curve" {
        let xs = (spec.start..=spec.end)
            .map(|c| {
                let text = cell(5, c).context("Missing humidity axis")?.to_string();
                Ok(text
                    .lines()
                    .last()
                    .context("Empty humidity heading")?
                    .parse::<f64>()?
                    / 100.0)
            })
            .collect::<Result<Vec<_>>>()?;
        pointers["axis"] = json!(format!("{prefix}{first}5:{last}5"));
        let curve = &obs["structured_value"];
        let equal = curve["x_unit"] == "-"
            && xs == numeric_array(&curve["x_values"])?
            && ys == numeric_array(&curve["y_values"])?;
        axes = Some(xs);
        equal
    } else {
        ys.len() == 1 && obs["value"].as_f64() == Some(ys[0])
    };
    audit["status"] = json!(if same { "identical" } else { "different" });
    if same {
        obs["conditions"]
            .as_object_mut()
            .unwrap()
            .extend(spec.condition.as_object().unwrap().clone());
        obs["conditions"]["workbook_evidence"] = pointers;
    } else {
        audit["workbook_values"] = json!(ys);
        if let Some(xs) = axes {
            audit["workbook_relative_humidity"] = json!(xs);
            audit["axis"] = pointers["axis"].clone();
        }
    }
    Ok(audit)
}

fn write_rows(path: &Path, rows: &[Value]) -> Result<()> {
    let mut tmp = NamedTempFile::new_in(path.parent().context("Missing bundle directory")?)?;
    for row in rows {
        serde_json::to_writer(&mut tmp, row)?;
        tmp.write_all(b"\n")?;
    }
    tmp.persist(path)?;
    Ok(())
}

pub fn run(args: Args) -> Result<Value> {
    let out = args.output.unwrap_or_else(|| args.root.join(SUBDIR));
    let mut sources = Vec::new();
    let mut archive = None;
    for (name, hash, timestamp, media) in FILES {
        let (source, bytes) = original(&args.root, name, hash, timestamp, media)?;
        if name == "materialProperties.zip" {
            archive = Some(bytes);
        }
        sources.push(source);
    }
    let mut zip = ZipArchive::new(Cursor::new(archive.context("Archive absent")?))?;
    let mut primary = String::new();
    zip.by_name(MEMBER)?.read_to_string(&mut primary)?;
    let mut xlsx = Vec::new();
    zip.by_name(BOOK)?.read_to_end(&mut xlsx)?;
    let mut book = Xlsx::new(Cursor::new(xlsx))?;
    let sheets = book.worksheets().into_iter().collect::<BTreeMap<_, _>>();
    let mut mats = Vec::new();
    let mut obs = Vec::new();
    let mut audit = Vec::new();
    let mut stats = BTreeMap::new();
    let mut props = BTreeMap::new();
    let mut matches = BTreeMap::new();
    let mut points = 0;
    for (id, row) in parse_specimens(&primary)? {
        mats.push(material(&id, &row)?);
        for key in FIELDS {
            let mut o = observation(&id, &row, key)?;
            if let Some(f) = field(key) {
                let a = reconcile(
                    &mut o,
                    &f,
                    sheets.get(f.sheet).context("Missing worksheet")?,
                )?;
                *matches
                    .entry(a["status"].as_str().unwrap().to_owned())
                    .or_insert(0) += 1;
                audit.push(a);
            }
            *stats
                .entry(o["value_kind"].as_str().unwrap().to_owned())
                .or_insert(0) += 1;
            *props.entry(key).or_insert(0) += 1;
            points += o["structured_value"]["y_values"]
                .as_array()
                .map_or(0, Vec::len);
            obs.push(o);
        }
    }
    let summary = json!({
        "dataset":"tampere","source_version":"1.0.0","doi":DOI,"attribution":ATTRIBUTION,"license":"CC BY 4.0","license_url":"https://creativecommons.org/licenses/by/4.0/",
        "sources":sources.len(),"materials":mats.len(),"observations":obs.len(),"scalar_values":stats["scalar"],"curves":stats["curve"],
        "explicitly_missing":stats["missing"],"curve_points":points,"workbook_comparisons":matches,"properties":props,
        "coverage":"All specimen records and all scalar and curve properties in primary allMaterialProperties.json. Relative humidity axes use fractions from 0 to 1. The independent wall time-series archive describes assemblies and is outside this material-property import.",
        "change":"The structured edition separates scalar properties and complete paired curves. It retains source units, specimen IDs, property names and the original files."
    });
    fs::create_dir_all(&out)?;
    for (name, rows) in [
        ("sources.jsonl", &sources),
        ("materials.jsonl", &mats),
        ("observations.jsonl", &obs),
        ("workbook-comparison.jsonl", &audit),
    ] {
        write_rows(&out.join(name), rows)?;
    }
    write_rows(&out.join("summary.json"), std::slice::from_ref(&summary))?;
    Ok(summary)
}
