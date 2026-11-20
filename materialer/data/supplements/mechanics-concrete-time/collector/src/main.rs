use anyhow::{Context, Result, ensure};
use calamine::{Data, Reader, Xlsx, open_workbook};
use flate2::{Compression, write::GzEncoder};
use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, File},
    io::{BufReader, Write},
    path::{Path, PathBuf},
};

const DATASET: &str = "mechanics-concrete-time";
const CREEP: &str = "mechanics-concrete-time:source:creep-workbook";
const FATIGUE: &str = "mechanics-concrete-time:source:fatigue-workbook";
type Book = Xlsx<BufReader<File>>;
type Index = BTreeMap<i64, Value>;
type Counts = BTreeMap<String, usize>;

fn cell(v: &Data) -> Result<Value> {
    Ok(match v {
        Data::Int(x) => json!(x),
        Data::Float(x) if x.is_finite() && x.fract() == 0.0 && x.abs() < (1u64 << 53) as f64 => {
            json!(*x as i64)
        }
        Data::Float(x) if x.is_finite() => json!(x),
        Data::Bool(x) => json!(x),
        Data::String(x) if x.is_empty() => Value::Null,
        Data::String(x) => json!(x),
        Data::Empty => Value::Null,
        Data::DateTime(x) => json!(x.to_string()),
        Data::DateTimeIso(x) | Data::DurationIso(x) => json!(x),
        _ => anyhow::bail!("Invalid numeric, date or text source cell {v:?}"),
    })
}

fn worksheet(book: &mut Book, name: &str, descriptions: &mut Value) -> Result<Vec<Value>> {
    let range = book.worksheet_range(name)?;
    let mut rows = range.rows();
    let keys: Vec<_> = rows
        .next()
        .context("Missing header")?
        .iter()
        .map(|s| s.to_string())
        .collect();
    let desc = rows.next().context("Missing data dictionary")?;
    descriptions[name] = Value::Object(
        keys.iter()
            .zip(desc)
            .map(|(k, v)| Ok((k.clone(), cell(v)?)))
            .collect::<Result<_>>()?,
    );
    rows.filter(|r| !r.first().is_none_or(|v| v == &Data::Empty))
        .map(|row| {
            let mut columns = Map::new();
            for (key, v) in keys.iter().zip(row) {
                let val = cell(v)?;
                if !val.is_null() {
                    columns.insert(key.clone(), val);
                }
            }
            Ok(Value::Object(columns))
        })
        .collect()
}

fn idx(rows: Vec<Value>, key: &str) -> Result<Index> {
    let mut out = Index::new();
    for row in rows {
        let id = number_id(&row, key)?;
        ensure!(
            out.insert(id, row).is_none(),
            "Duplicate primary key {key}={id}"
        );
    }
    Ok(out)
}
fn number_id(v: &Value, key: &str) -> Result<i64> {
    v[key]
        .as_i64()
        .with_context(|| format!("Missing integer key {key} in {v}"))
}
fn increase(counts: &mut Counts, key: &str) {
    *counts.entry(key.into()).or_default() += 1;
}

struct Output {
    mats: GzEncoder<File>,
    facts: GzEncoder<File>,
    obs: GzEncoder<File>,
    subjects: BTreeSet<String>,
    fields: Counts,
}
fn writer(root: &Path, name: &str) -> Result<GzEncoder<File>> {
    Ok(GzEncoder::new(
        File::create(root.join(format!("{name}.jsonl.gz")))?,
        Compression::default(),
    ))
}
fn line(out: &mut GzEncoder<File>, v: &Value) -> Result<()> {
    serde_json::to_writer(&mut *out, v)?;
    out.write_all(b"\n")?;
    Ok(())
}
impl Output {
    fn subject(
        &mut self,
        id: &str,
        name: String,
        category: &str,
        source: &str,
        loc: &str,
    ) -> Result<()> {
        ensure!(self.subjects.insert(id.into()), "Duplicate subject {id}");
        line(
            &mut self.mats,
            &json!({"id":id,"name":name,"category":category,"aliases":["cementbaseret materiale","cementitious material"],"entity_kind":"specimen_group","kind":"generic","source_id":source,"source_locator":loc}),
        )
    }
    fn pair(
        &mut self,
        subject: &str,
        key: &str,
        field: &str,
        value: Value,
        unit: &str,
        source: &str,
        loc: &str,
        conditions: &Value,
    ) -> Result<()> {
        let id = format!("{subject}:{key}");
        let mut common = json!({"material_id":subject,"source_id":source,"source_locator":loc,"unit":unit,"conditions":conditions});
        common["id"] = json!(id);
        common["field_id"] = json!(field);
        common["value_status"] = json!("reported");
        common["value"] = value;
        line(&mut self.facts, &common)?;
        let obs_value = common.as_object_mut().unwrap().remove("value").unwrap();
        common.as_object_mut().unwrap().remove("field_id");
        common.as_object_mut().unwrap().remove("value_status");
        common["property"] = json!(field);
        common["id"] = json!(format!("{id}:observation"));
        common["data_status"] = json!("reported");
        if obs_value.is_number() {
            common["value_text"] = json!(obs_value.to_string());
            common["value"] = obs_value;
        } else {
            common["value_text"] = json!(format!(
                "{} source measurements",
                obs_value["x_values"]
                    .as_array()
                    .context("Missing axis")?
                    .len()
            ));
            common["value_kind"] = json!("curve");
            common["value"] = Value::Null;
            common["structured_value"] = obs_value;
        }
        line(&mut self.obs, &common)?;
        increase(&mut self.fields, field);
        Ok(())
    }
}

struct Rel {
    specimens: Index,
    mixes: Index,
    literature: Index,
    refs: BTreeMap<i64, Vec<i64>>,
}
impl Rel {
    fn read(book: &mut Book, desc: &mut Value) -> Result<Self> {
        let specimens = idx(worksheet(book, "specimen", desc)?, "S_id")?;
        let mixes = idx(worksheet(book, "mix", desc)?, "M_id")?;
        let literature = idx(worksheet(book, "literature", desc)?, "L_id")?;
        let mut refs: BTreeMap<i64, Vec<i64>> = BTreeMap::new();
        for row in worksheet(book, "literature_to_mix", desc)? {
            let m = number_id(&row, "LM_M_id")?;
            let l = number_id(&row, "LM_L_id")?;
            ensure!(
                mixes.contains_key(&m) && literature.contains_key(&l),
                "Unresolved bibliography link M{m} to L{l}"
            );
            refs.entry(m).or_default().push(l);
        }
        Ok(Self {
            specimens,
            mixes,
            literature,
            refs,
        })
    }
    fn citations(&self, m: i64) -> Vec<&Value> {
        self.refs
            .get(&m)
            .into_iter()
            .flatten()
            .map(|l| &self.literature[l])
            .collect()
    }
}
struct Series<'a> {
    prefix: &'a str,
    test_prefix: &'a str,
    table: &'a str,
    type_key: &'a str,
    value_key: &'a str,
    field: &'a str,
    unit: &'a str,
}
fn curves(
    book: &mut Book,
    rel: &Rel,
    out: &mut Output,
    desc: &mut Value,
    s: Series,
) -> Result<Counts> {
    let dp = s.prefix;
    let tp = s.test_prefix;
    let data_name = format!("{}_data", s.table);
    let test_name = format!("{}_test", s.table);
    let test_key = format!("{tp}_id");
    let data_key = format!("{dp}_id");
    let foreign_key = format!("{dp}_{tp}_id");
    let x_key = format!("{dp}_dt");
    let flag_key = format!("{dp}_elimData");
    let type_flag = format!("{}_CTU", s.type_key);
    let tests = idx(worksheet(book, &test_name, desc)?, &test_key)?;
    let points = idx(worksheet(book, &data_name, desc)?, &data_key)?;
    let mut grouped: BTreeMap<i64, Vec<(f64, f64, i64, Value)>> = BTreeMap::new();
    let mut stats = Counts::new();
    stats.insert("source_tests".into(), tests.len());
    stats.insert("source_rows".into(), points.len());
    for (id, mut p) in points {
        let t = number_id(&p, &foreign_key)?;
        let test = tests
            .get(&t)
            .with_context(|| format!("No parent test for {data_name} {id}"))?;
        if test[&type_flag]
            .as_str()
            .is_some_and(|v| v.contains("ERROR"))
        {
            increase(&mut stats, "excluded_rows_test_ERROR");
            continue;
        }
        match &p[&flag_key] {
            v if v.is_null() || *v == 0 || *v == false => (),
            v if *v == 1 || *v == true => {
                increase(&mut stats, "excluded_rows_suspicious_point");
                continue;
            }
            other => anyhow::bail!("Unexpected exclusion marker {other} in {data_name} {id}"),
        }
        let (Some(x), Some(y)) = (p[&x_key].as_f64(), p[s.value_key].as_f64()) else {
            increase(&mut stats, "excluded_rows_missing_numeric_pair");
            continue;
        };
        let obj = p.as_object_mut().unwrap();
        for k in [&*data_key, &*foreign_key, &*x_key, s.value_key] {
            obj.remove(k);
        }
        grouped.entry(t).or_default().push((x, y, id, p));
    }
    for (t, mut data) in grouped {
        data.sort_by(|a, b| a.0.total_cmp(&b.0).then(a.2.cmp(&b.2)));
        let (mut x, mut y, mut row_ids, mut attrs) = (vec![], vec![], vec![], Map::new());
        for (time, v, id, extras) in data {
            if x.last() == Some(&time) {
                increase(&mut stats, "repeated_time_points");
            }
            if time < 0.0 {
                increase(&mut stats, "negative_time_points");
            }
            x.push(time);
            y.push(v);
            row_ids.push(id);
            if !extras.as_object().unwrap().is_empty() {
                attrs.insert(id.to_string(), extras);
            }
            increase(&mut stats, "retained_rows");
        }
        increase(&mut stats, "retained_curves");
        let test = &tests[&t];
        let sp = number_id(test, &format!("{tp}_S_id"))?;
        let specimen = rel.specimens.get(&sp).context("Unknown specimen")?;
        let mix_id = number_id(specimen, "S_M_id")?;
        let mix = rel.mixes.get(&mix_id).context("Unknown mix")?;
        let ty = test[s.type_key]
            .as_str()
            .unwrap_or("unknown")
            .trim_end_matches('?');
        let axis = match (s.table, ty) {
            ("creep", "basic" | "total") => "days_since_mechanical_loading",
            ("creep", "drying") | ("shrinkage", "total" | "drying shrinkage") => {
                "days_since_drying_exposure"
            }
            ("shrinkage", "autogenous") => "days_since_recorded_autogenous_zero",
            _ => "source_elapsed_days_origin_unspecified",
        };
        let loc = format!(
            "{data_name}: {foreign_key}={t}, columns {x_key}/{}, ordered {data_key} in source_point_ids; {test_name}: {test_key}={t}; specimen S_id={sp}; mix M_id={mix_id}",
            s.value_key
        );
        let subject = format!("{DATASET}:material:{}-{t}", s.table);
        let label = if s.table == "creep" {
            "Krybning"
        } else {
            "Svind"
        };
        out.subject(
            &subject,
            format!("{label} · {} {t} · blanding {mix_id}", test_key),
            "Cementbaserede materialer / tidsafhængige laboratorieforsøg",
            CREEP,
            &loc,
        )?;
        let source_quality = match test[&type_flag].as_str() {
            Some(flag) if flag.ends_with('?') => "problematic (source question mark)",
            Some("basic" | "total" | "drying" | "autogenous" | "drying shrinkage") => {
                "plausible (source unmarked type)"
            }
            _ => "unclassified",
        };
        let quantity = match (s.table, ty) {
            ("creep", "total" | "basic") => {
                "Reported compliance function. Total load-induced compliance includes the instantaneous elastic and delayed strain per unit stress. CT_elastic_strain describes whether initial strain was measured. Missing or false flags do not establish that the published values include or exclude an elastic offset."
            }
            ("creep", "drying") => {
                "Reported drying-creep component per unit stress. Refer to study for separation of basic creep or shrinkage."
            }
            ("creep", _) => "Reported creep function per unit stress; component unspecified.",
            _ => "Signed shrinkage strain, with contraction negative and expansion positive.",
        };
        let cond = json!({
            "design_value":false,
            "test":test,
            "specimen":specimen,
            "mix":mix,
            "literature":rel.citations(mix_id),
            "source_point_ids":row_ids,
            "point_attributes_by_id":attrs,
            "source_quality_class":source_quality,
            "quantity_basis":quantity,
            "x_definition_as_published":desc[&data_name][&x_key],
            "y_definition_as_published":desc[&data_name][s.value_key],
            "uncertainty":"No per-point uncertainty or characteristic value assigned.",
            "transform":"Unshifted source x and y, sorted by source time and point ID."
        });
        let value = json!({"x_property":axis,"x_unit":"d","x_values":x,"y_property":s.value_key,"y_unit":s.unit,"y_values":y});
        out.pair(
            &subject, "curve", s.field, value, s.unit, CREEP, &loc, &cond,
        )?;
    }
    let accounted = stats["retained_rows"]
        + stats
            .iter()
            .filter(|(s, _)| s.starts_with("excluded_rows_"))
            .map(|(_, n)| n)
            .sum::<usize>();
    ensure!(
        accounted == stats["source_rows"],
        "Incomplete point accounting"
    );
    Ok(stats)
}
fn strengths(rel: &Rel, out: &mut Output) -> Result<()> {
    for (m, mix) in &rel.mixes {
        let quantities = [
            ("M_fcmCyl28d", "compressive_strength", "mean cylinder"),
            ("M_fcmCube28d", "compressive_strength", "mean cube"),
            (
                "M_ElasticMod28",
                "elastic_modulus",
                "modulus of elasticity, specimen geometry unspecified",
            ),
        ];
        let subject = format!("{DATASET}:material:mix-{m}");
        let loc = format!("mix: M_id={m}");
        let mut seen = false;
        for (key, field, basis) in quantities {
            let Some(v) = mix[key].as_f64() else { continue };
            if v <= 0.0 {
                continue;
            }
            if !seen {
                out.subject(
                    &subject,
                    format!("Cementbaseret blanding {m} · 28 døgn"),
                    "Cementbaserede materialer / laboratorieblanding",
                    CREEP,
                    &loc,
                )?;
                seen = true;
            }
            let cond = json!({"age_days":28,"basis":basis,"design_value":false,"mix":mix,"literature":rel.citations(*m)});
            out.pair(
                &subject,
                key,
                field,
                mix[key].clone(),
                "MPa",
                CREEP,
                &format!("{loc}; column {key}"),
                &cond,
            )?;
        }
    }
    Ok(())
}
fn fatigue(path: &Path, out: &mut Output, desc: &mut Value) -> Result<()> {
    let mut book: Book = open_workbook(path)?;
    let range = book.worksheet_range("Sample details")?;
    let mut rows = range.rows();
    let (header, units) = (
        rows.next().context("Missing headings")?,
        rows.next().context("Missing units")?,
    );
    let keys: Vec<_> = header
        .iter()
        .map(|c| c.to_string().trim().to_owned())
        .collect();
    let units: Map<_, _> = keys
        .iter()
        .cloned()
        .zip(units.iter().map(|v| json!(v.to_string())))
        .skip(1)
        .collect();
    desc["fatigue_sample_details_units"] = Value::Object(units);
    let mut in_fatigue = false;
    let mut seen = 0;
    for (i, r) in rows.enumerate() {
        let name = r.first().context("Missing test identifier")?.to_string();
        if name == "Fatigue" {
            in_fatigue = true;
            continue;
        }
        if !in_fatigue || name.is_empty() {
            continue;
        }
        let values: Map<_, _> = keys
            .iter()
            .zip(r)
            .skip(1)
            .map(|(k, v)| Ok((k.clone(), cell(v)?)))
            .collect::<Result<_>>()?;
        let n = &values["N"];
        ensure!(
            n.as_i64().is_some_and(|n| n > 0) && values["f"].as_f64().is_some_and(|x| x > 0.0),
            "Invalid fatigue trial {name}"
        );
        for k in ["Pmax", "Pmin", "Pa", "Pmean", "Stress"] {
            ensure!(values[k].is_number(), "Missing load data {name}, {k}");
        }
        let subject = format!(
            "{DATASET}:material:{}",
            name.to_lowercase().replace('_', "-")
        );
        let loc = format!(
            "Sample details, row {} (B:N), specimen {} under Fatigue",
            i + 3,
            name
        );
        out.subject(
            &subject,
            format!("Højstyrkebeton · {name}"),
            "Beton / udmattelsesforsøg",
            FATIGUE,
            &loc,
        )?;
        let cond = json!({"design_value":false,"specimen_id":name,"original_values":values,"original_units":desc["fatigue_sample_details_units"],"quantity_basis":"number of cycles N as recorded","endpoint":"failure vs runout not identified per row in workbook","article_doi":"10.1016/j.cemconcomp.2025.106394"});
        out.pair(
            &subject,
            "cycles",
            "fatigue_resistance",
            n.clone(),
            "cycles",
            FATIGUE,
            &loc,
            &cond,
        )?;
        seen += 1;
    }
    ensure!(seen == 16, "Unexpected fatigue specimen count {seen}");
    Ok(())
}
fn main() -> Result<()> {
    let root = PathBuf::from(
        std::env::args_os()
            .nth(1)
            .context("Pass the supplement directory")?,
    );
    for line in fs::read_to_string(root.join("sources.jsonl"))?.lines() {
        let source: Value = serde_json::from_str(line)?;
        let fname = Path::new(
            source["local_path"]
                .as_str()
                .context("Missing source file")?,
        )
        .file_name()
        .unwrap();
        let bytes = fs::read(root.join("originals").join(fname))?;
        ensure!(
            source["sha256"] == format!("{:x}", Sha256::digest(bytes)),
            "Original hash mismatch for {fname:?}"
        );
    }
    let mut book: Book = open_workbook(root.join("originals/CreepShrinkage-2023-07-15-xlsx.xlsx"))?;
    let mut desc = json!({});
    let rel = Rel::read(&mut book, &mut desc)?;
    let staging = tempfile::Builder::new()
        .prefix(".concrete-import-")
        .tempdir_in(&root)?;
    let mut out = Output {
        mats: writer(staging.path(), "materials")?,
        facts: writer(staging.path(), "facts")?,
        obs: writer(staging.path(), "observations")?,
        subjects: BTreeSet::new(),
        fields: Counts::new(),
    };
    let creep = curves(
        &mut book,
        &rel,
        &mut out,
        &mut desc,
        Series {
            prefix: "CD",
            test_prefix: "CT",
            table: "creep",
            type_key: "CT_creepType",
            value_key: "CD_Jcreep",
            field: "creep",
            unit: "µstrain/MPa",
        },
    )?;
    let shrinkage = curves(
        &mut book,
        &rel,
        &mut out,
        &mut desc,
        Series {
            prefix: "SD",
            test_prefix: "ST",
            table: "shrinkage",
            type_key: "ST_shrinkageType",
            value_key: "SD_strain",
            field: "shrinkage_strain_time",
            unit: "µstrain",
        },
    )?;
    strengths(&rel, &mut out)?;
    fatigue(
        &root.join("originals/Test details.xlsx"),
        &mut out,
        &mut desc,
    )?;
    let total: usize = out.fields.values().sum();
    let summary = json!({"dataset":DATASET,"title":"Laboratory creep, shrinkage, mix strength and cyclic loading of cementitious materials","sources":4,"materials":out.subjects.len(),"observations":total,"facts":total,"facts_by_field":out.fields,"creep":creep,"shrinkage":shrinkage,"documentation":"data/supplements/mechanics-concrete-time/README.md"});
    out.mats.finish()?;
    out.facts.finish()?;
    out.obs.finish()?;
    for (name, v) in [("source-columns.json", desc), ("summary.json", summary)] {
        let mut file = File::create(staging.path().join(name))?;
        serde_json::to_writer_pretty(&mut file, &v)?;
        file.write_all(b"\n")?;
    }
    for name in [
        "materials.jsonl.gz",
        "observations.jsonl.gz",
        "facts.jsonl.gz",
        "source-columns.json",
        "summary.json",
    ] {
        fs::rename(staging.path().join(name), root.join(name))?;
    }
    Ok(())
}
