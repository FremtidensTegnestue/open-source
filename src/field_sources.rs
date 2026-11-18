//! Rebuild the field supplement from the pinned original publications.
use anyhow::{Context, Result, bail, ensure};
use calamine::{Data, Reader, open_workbook_auto};
use flate2::{Compression, write::GzEncoder};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, HashSet},
    fs::{self, File},
    io::{BufRead, BufReader, BufWriter, Write},
    path::Path,
};

const DIR: &str = "data/supplements/field-sources";
const PREFIX: &str = "field-sources:";
type Stream = GzEncoder<BufWriter<File>>;

fn required<'a>(v: &'a Value, key: &str) -> Result<&'a str> {
    v[key].as_str().with_context(|| format!("Missing {key}"))
}
fn stream(dir: &Path, name: &str) -> Result<Stream> {
    Ok(GzEncoder::new(
        BufWriter::new(File::create(dir.join(format!("{name}.jsonl.gz")))?),
        Compression::default(),
    ))
}
fn write_row(writer: &mut impl Write, row: &Value) -> Result<()> {
    serde_json::to_writer(&mut *writer, row)?;
    writer.write_all(b"\n")?;
    Ok(())
}

struct Bundle {
    materials: Stream,
    facts: Stream,
    observations: Stream,
    subjects: HashSet<String>,
    by_field: BTreeMap<String, usize>,
    observations_count: usize,
}

struct Subject {
    id: String,
    source: String,
}

impl Bundle {
    fn subject(
        &mut self,
        key: &str,
        name: &str,
        category: &str,
        kind: &str,
        source: &str,
        locator: &str,
    ) -> Result<Subject> {
        let id = format!("{PREFIX}material:{key}");
        ensure!(self.subjects.insert(id.clone()), "Duplicate subject {id}");
        let entry_kind = match kind {
            "element" | "reference_material" => "product",
            "assembly" => "assembly",
            _ => "generic",
        };
        write_row(
            &mut self.materials,
            &json!({
                "id": id,
                "name": name,
                "category": category,
                "kind": entry_kind,
                "entity_kind": kind,
                "source_id": source,
                "source_locator": locator,
            }),
        )?;
        Ok(Subject {
            id,
            source: source.into(),
        })
    }

    #[expect(
        clippy::too_many_arguments,
        reason = "The source adapters explicitly pair each field with its unit, locator and conditions"
    )]
    fn fact(
        &mut self,
        m: &Subject,
        field: &str,
        key: &str,
        value: Value,
        unit: Option<&str>,
        locator: &str,
        conditions: &Value,
    ) -> Result<()> {
        let id = format!("{}:{field}:{key}", m.id);
        write_row(
            &mut self.facts,
            &json!({
                "id": id,
                "material_id": m.id,
                "field_id": field,
                "value": value,
                "unit": unit,
                "source_id": m.source,
                "source_locator": locator,
                "conditions": conditions,
                "value_status": "reported",
            }),
        )?;
        *self.by_field.entry(field.into()).or_default() += 1;
        // Numeric observations remain available to the original property/calculation commands.
        // Text, classifications and heterogeneous records use the native field representation.
        if value.is_number() || value.get("x_values").is_some() {
            let curve = value.is_object();
            let value_text = if curve {
                format!(
                    "{} points",
                    value["x_values"]
                        .as_array()
                        .context("Missing curve axis")?
                        .len()
                )
            } else {
                conditions["source_value_text"]
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| value.to_string())
            };
            let mut obs = json!({
                "id": format!("{id}:observation"),
                "material_id": m.id,
                "property": field,
                "unit": unit,
                "value_text": value_text,
                "value_kind": if curve {"curve"} else {"scalar"},
                "source_id": m.source,
                "source_locator": locator,
                "conditions": conditions,
                "data_status": "reported",
            });
            if curve {
                obs["structured_value"] = value
            } else {
                obs["value"] = value;
            }
            write_row(&mut self.observations, &obs)?;
            self.observations_count += 1;
        }
        Ok(())
    }
}

fn cell_value(d: &Data) -> Result<Value> {
    Ok(match d {
        Data::Int(x) => json!(x),
        Data::Float(x) if x.is_finite() => json!(x),
        Data::String(x) => json!(x.trim()),
        Data::Bool(x) => json!(x),
        Data::Empty => Value::Null,
        _ => bail!("Unexpected spreadsheet cell: {d}"),
    })
}

fn inventory(bundle: &mut Bundle, path: &Path, source: &str) -> Result<()> {
    let mut book = open_workbook_auto(path)?;
    let sheet = book.sheet_names()[0].clone();
    let range = book.worksheet_range(&sheet)?;
    let mut rows = range.rows();
    let headers: Vec<_> = rows
        .next()
        .context("Missing element headers")?
        .iter()
        .map(ToString::to_string)
        .collect();
    ensure!(
        headers[0] == sheet && headers[1] == "Building ID",
        "Unrecognised element table"
    );
    for (i, row) in rows.enumerate() {
        if row[0] == Data::Empty {
            continue;
        }
        let original_id = row[0].to_string();
        let locator = format!("'{sheet}'!A{}", i + 2);
        let element_type = row[4].to_string();
        let m = bundle.subject(
            &format!("recreate-{original_id}"),
            &format!("{element_type} · {original_id}"),
            "Genbrugte betonelementer",
            "element",
            source,
            &locator,
        )?;
        let mut record = serde_json::Map::new();
        for (header, d) in headers.iter().zip(row) {
            if !header.is_empty() && *d != Data::Empty {
                record.insert(header.clone(), cell_value(d)?);
            }
        }
        let location = format!(
            "'{sheet}'!A{}:{}{}",
            i + 2,
            char::from(b'A' + (headers.len() - 1) as u8),
            i + 2
        );
        let conditions = json!({
            "donor_element_id": original_id,
            "donor_building_id": record["Building ID"],
            "evidence_type": "reported donor inventory",
            "published": "2025-08-12",
            "interpretation": "Pilot registration. Consult the evidence and notes before specifying reuse.",
        });
        bundle.fact(
            &m,
            "reuse_evidence",
            "inventory",
            Value::Object(record.clone()),
            None,
            &location,
            &conditions,
        )?;
        let intervention = record
            .get("Intervention Class")
            .context("Missing intervention class")?;
        let grade = json!({
            "intervention_class": intervention,
            "has_damage": record.get("Has Damage"),
            "notes": record.get("Notes"),
        });
        bundle.fact(
            &m,
            "condition_grade",
            "inventory",
            grade,
            None,
            &location,
            &conditions,
        )?;
        if let Some(coating) = record.get("Coating Layer") {
            bundle.fact(
                &m,
                "surface_finish",
                "coating",
                coating.clone(),
                None,
                &location,
                &conditions,
            )?;
        }
    }
    Ok(())
}

const CONCRETE: &[(usize, &str, &str)] = &[
    (4, "compressive_strength", "MPa"),
    (5, "compressive_strength", "MPa"),
    (7, "tensile_strength", "MPa"),
    (8, "tensile_strength", "MPa"),
    (9, "elastic_modulus", "GPa"),
    (11, "thermal_expansion_coefficient", "1/K"),
    (12, "density", "kg/m³"),
    (13, "poisson_ratio", "1"),
];
const STEEL: &[(usize, &str, &str)] = &[
    (4, "yield_strength", "MPa"),
    (5, "tensile_strength", "MPa"),
    (6, "elastic_modulus", "GPa"),
    (12, "surface_finish", ""),
    (13, "thermal_expansion_coefficient", "1/K"),
];

fn grades(bundle: &mut Bundle, path: &Path, source: &str, kind: &str) -> Result<()> {
    let mut book = open_workbook_auto(path)?;
    let sheet = book.sheet_names()[0].clone();
    let range = book.worksheet_range(&sheet)?;
    let mut rows = range.rows();
    let headers = rows.next().context("Missing class headers")?;
    ensure!(
        headers.len() == 15 && headers[0] == "Country",
        "Unknown material library"
    );
    let concrete = kind == "concrete";
    for (i, row) in rows.enumerate() {
        if row[3] == Data::Empty {
            continue;
        }
        let n = i + 2;
        let name = row[3].to_string();
        let m = bundle.subject(
            &format!("recreate-{kind}-{n}"),
            &format!(
                "{} {} ({}, {})",
                if concrete { "Beton" } else { "Armeringsstål" },
                name,
                row[0],
                row[2]
            ),
            if concrete {
                "Betonklasser"
            } else {
                "Stålklasser"
            },
            "material_class",
            source,
            &format!("'{sheet}'!D{n}"),
        )?;
        let mut conditions = json!({
            "country": cell_value(&row[0])?,
            "standard_as_reported": cell_value(&row[1])?,
            "year_as_reported": cell_value(&row[2])?,
            "grade": name,
            "source_notes": cell_value(&row[14])?,
            "evidence_type": "published reference library",
        });
        if concrete {
            conditions["measurement_method"] = cell_value(&row[6])?;
        }
        for &(col, field, unit) in if concrete { CONCRETE } else { STEEL } {
            if row[col] == Data::Empty {
                continue;
            }
            let value = cell_value(&row[col])?;
            let value = value
                .as_str()
                .and_then(|v| v.parse::<f64>().ok())
                .filter(|v| v.is_finite())
                .map(|v| json!(v))
                .unwrap_or(value);
            let letter = char::from(b'A' + col as u8);
            conditions["source_column"] = json!(headers[col].to_string());
            conditions["source_value_text"] = json!(row[col].to_string());
            bundle.fact(
                &m,
                field,
                &letter.to_string(),
                value,
                (!unit.is_empty()).then_some(unit),
                &format!("'{sheet}'!{letter}{n}"),
                &conditions,
            )?;
        }
    }
    Ok(())
}

fn glazing(bundle: &mut Bundle, path: &Path, source: &str) -> Result<()> {
    let text = fs::read_to_string(path)?;
    let fields = [
        (3, "thickness", "m"),
        (5, "solar_reflectance", "1"),
        (6, "solar_reflectance", "1"),
        (7, "visible_light_transmittance", "1"),
        (8, "visible_reflectance", "1"),
        (9, "visible_reflectance", "1"),
        (11, "longwave_emissivity", "1"),
        (12, "longwave_emissivity", "1"),
        (13, "thermal_conductivity", "W/(m·K)"),
    ];
    let lines: Vec<_> = text.lines().collect();
    for (i, line) in lines.iter().enumerate() {
        if line.trim() != "WindowMaterial:Glazing," {
            continue;
        }
        let cells = lines
            .get(i + 1..=i + 14)
            .context("Incomplete glazing record")?;
        let parsed: Vec<_> = cells
            .iter()
            .map(|line| {
                let (v, label) = line.split_once("!-").context("Missing IDF field label")?;
                Ok::<_, anyhow::Error>((v.trim().trim_end_matches([',', ';']).trim(), label.trim()))
            })
            .collect::<Result<_>>()?;
        ensure!(
            parsed[0].1 == "Name"
                && parsed[1].0 == "SpectralAverage"
                && parsed[13].1.starts_with("Conductivity"),
            "Unexpected glazing record"
        );
        let name = parsed[0].0;
        let m = bundle.subject(
            &format!("energyplus-glass-{}", i + 1),
            name,
            "Rudelag, EnergyPlus-reference",
            "simulation_material",
            source,
            &format!("line {}, Name", i + 2),
        )?;
        for (col, field, unit) in fields {
            let (s, label) = parsed[col];
            let n = s.parse::<f64>()?;
            ensure!(n.is_finite(), "Non-finite glass property");
            let conditions = json!({
                "source_field": label,
                "source_value_text": s,
                "glazing": name,
                "optical_data_type": "SpectralAverage",
                "side_convention": "front faces away from the modelled zone; back faces the zone",
                "evidence_type": "simulation reference input",
            });
            bundle.fact(
                &m,
                field,
                &col.to_string(),
                json!(n),
                Some(unit),
                &format!(
                    "line {}, WindowMaterial:Glazing '{}', {}",
                    i + col + 2,
                    name,
                    label
                ),
                &conditions,
            )?;
        }
    }
    Ok(())
}

fn acoustic(bundle: &mut Bundle, path: &Path, source: &str) -> Result<()> {
    let folder = path.parent().context("Missing original directory")?;
    let labels = fs::read_to_string(folder.join("target1.csv"))?;
    let mut targets = labels.trim_start_matches('\u{feff}').lines();
    let axis: Vec<_> = (0..2561).map(|i| 250.0 + i as f64 * 1.5625).collect();
    let mut subjects = BTreeMap::new();
    let mut count = 0;
    for (i, line) in BufReader::new(File::open(path)?).lines().enumerate() {
        let line = line?;
        let row = i + 1;
        let target = targets
            .next()
            .context("Missing acoustic measurement conditions")?;
        let flags: Vec<_> = target.split(',').map(str::trim).collect();
        ensure!(
            flags.len() == 14 && flags.iter().all(|s| matches!(*s, "0" | "1")),
            "Invalid flags on row {row}"
        );
        let mut active = vec![];
        for g in [
            &flags[0..2],
            &flags[2..4],
            &flags[4..7],
            &flags[7..11],
            &flags[11..14],
        ] {
            ensure!(
                g.iter().filter(|&&v| v == "1").count() == 1,
                "Expected one value per experimental factor on row {row}"
            );
            active.push(g.iter().position(|v| *v == "1").unwrap());
        }
        let name = ["Green", "Grey"][active[0]];
        let sample = active[4] + 1;
        let key = format!("{name}-{sample}");
        if !subjects.contains_key(&key) {
            let m = bundle.subject(
                &format!("acoustic-{key}"),
                &format!("Impedansrør · {name}, prøve {sample}"),
                "Akustiske laboratorieprøver",
                "specimen_group",
                source,
                &format!(
                    "alpha1.csv row {row}; paired target1.csv row {row}; Read_Me_dataset1.pdf p. 1"
                ),
            )?;
            subjects.insert(key.clone(), m);
        }
        let y: Vec<_> = line
            .trim_start_matches('\u{feff}')
            .split(", ")
            .map(|s| s.trim().replace(',', ".").parse::<f64>())
            .collect::<std::result::Result<_, _>>()?;
        ensure!(
            y.len() == axis.len() && y.iter().all(|v| v.is_finite()),
            "Invalid frequency curve on row {row}"
        );
        let cond = json!({
            "material_code": name,
            "specimen_number": sample,
            "protective_layer": (["SI","NO"][active[1]]),
            "installation_configuration": (["T1","T2","T3"][active[2]]),
            "relative_humidity_percent": ([10,40,70,100][active[3]]),
            "measurement_row": row,
            "method": "impedance tube",
            "evidence_type": "measured",
            "conditions_source_id": "field-sources:source:target1",
            "conditions_source_locator": format!("target1.csv row {row}, columns 1–14"),
            "axis_source_id": "field-sources:source:read_me_dataset1",
            "axis_source_locator": "Read_Me_dataset1.pdf p. 1, frequency range and resolution",
        });
        let curve = json!({
            "x_property": "frequency",
            "x_unit": "Hz",
            "x_values": axis,
            "y_values": y,
        });
        bundle.fact(
            &subjects[&key],
            "sound_absorption_coefficient",
            &row.to_string(),
            curve,
            Some("1"),
            &format!("alpha1.csv row {row}, all 2561 frequency bins"),
            &cond,
        )?;
        count += 1;
    }
    ensure!(
        count == 648 && targets.next().is_none(),
        "Unexpected acoustic row count"
    );
    Ok(())
}

fn manual(bundle: &mut Bundle, source: &str, recipe: &[Value]) -> Result<()> {
    for row in recipe
        .iter()
        .filter(|r| r["source"] == source.trim_start_matches("field-sources:source:"))
    {
        let m = bundle.subject(
            required(row, "key")?,
            required(row, "name")?,
            required(row, "category")?,
            required(row, "kind")?,
            source,
            required(row, "locator")?,
        )?;
        for e in row["entries"]
            .as_array()
            .context("Missing manual entries")?
        {
            bundle.fact(
                &m,
                required(e, "field")?,
                required(e, "key")?,
                e["value"].clone(),
                e["unit"].as_str(),
                required(e, "locator")?,
                &e["conditions"],
            )?;
        }
    }
    Ok(())
}

pub fn collect(root: &Path) -> Result<Value> {
    let folder = root.join(DIR);
    let archive: Vec<Value> = serde_json::from_slice(&fs::read(folder.join("archive.json"))?)?;
    let recipe: Vec<Value> = serde_json::from_slice(&fs::read(folder.join("transcription.json"))?)?;
    // Verify all inputs before reading cross-file dependencies or changing any public files.
    for s in &archive {
        let path = root.join(required(s, "local_path")?);
        ensure!(
            crate::store::file_hash(&path)? == required(s, "sha256")?,
            "Original checksum failed for {}",
            path.display()
        );
    }
    let staging = tempfile::tempdir_in(&folder)?;
    let temp = staging.path();
    let mut bundle = Bundle {
        materials: stream(temp, "materials")?,
        facts: stream(temp, "facts")?,
        observations: stream(temp, "observations")?,
        subjects: HashSet::new(),
        by_field: BTreeMap::new(),
        observations_count: 0,
    };
    let mut sources = BufWriter::new(File::create(temp.join("sources.jsonl"))?);
    for s in &archive {
        let source = required(s, "id")?;
        let path = root.join(required(s, "local_path")?);
        write_row(&mut sources, s)?;
        match required(s, "import")? {
            "inventory" => inventory(&mut bundle, &path, source)?,
            k @ ("concrete" | "steel") => grades(&mut bundle, &path, source, k)?,
            "glazing" => glazing(&mut bundle, &path, source)?,
            "acoustic" => acoustic(&mut bundle, &path, source)?,
            "manual" => manual(&mut bundle, source, &recipe)?,
            "context" => {}
            k => bail!("Unknown field source role {k}"),
        }
    }
    let summary = json!({
        "dataset": "field-sources",
        "sources": archive.len(),
        "materials": bundle.subjects.len(),
        "observations": bundle.observations_count,
        "facts": bundle.by_field.values().sum::<usize>(),
        "facts_by_field": bundle.by_field,
        "acoustic_frequency_points": 648*2561,
        "documentation": "docs/sources/field-sources.md",
    });
    sources.flush()?;
    for stream in [bundle.materials, bundle.observations, bundle.facts] {
        stream.finish()?.flush()?;
    }
    fs::write(
        temp.join("summary.json"),
        serde_json::to_string_pretty(&summary)? + "\n",
    )?;
    for name in [
        "sources.jsonl",
        "materials.jsonl.gz",
        "observations.jsonl.gz",
        "facts.jsonl.gz",
        "summary.json",
    ] {
        fs::rename(temp.join(name), folder.join(name))?;
    }
    Ok(summary)
}
