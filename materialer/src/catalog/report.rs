use super::{FIELDS, INDEX, evidence::*, fingerprint};
use crate::{query, store::Edition};
use anyhow::{Context, Result, ensure};
use rusqlite::{params_from_iter, types::Value as Sql};
use serde_json::{Value, json};
use std::collections::{BTreeMap, HashMap};

fn filters(
    material: Option<&str>,
    dataset: Option<&str>,
    material_column: &str,
    dataset_column: &str,
) -> (String, Vec<Sql>) {
    let mut conditions = vec![];
    let mut params = vec![];
    for (value, column) in [(material, material_column), (dataset, dataset_column)] {
        if let Some(v) = value {
            conditions.push(format!("{column}=?"));
            params.push(v.to_owned().into());
        }
    }
    let sql = if conditions.is_empty() {
        String::new()
    } else {
        format!(" WHERE {}", conditions.join(" AND "))
    };
    (sql, params)
}

fn materials(e: &Edition, material: Option<&str>, dataset: Option<&str>) -> Result<Vec<Value>> {
    let (clause, params) = filters(material, dataset, "m.id", "m.dataset_id");
    let mut out = vec![];
    for schema in ["foundation", "extra"] {
        let sql = format!(
            "SELECT {MATERIAL_COLUMNS} FROM {schema}.unified_materials m
            JOIN {schema}.sources s ON s.id=m.source_id {clause}"
        );
        out.extend(query::rows(&e.db, &sql, params.clone())?);
    }
    Ok(out)
}

fn details(origin: &str, row: &Value, value: Value) -> Value {
    json!({"origin":origin,"record_id":row["id"],"value":value,"source_id":row["source_id"],
        "source_locator":row["source_locator"],"source_version_id":row["source_version_id"],"source_url":row["source_url"]})
}

struct Page<'a> {
    field: Option<&'a str>,
    limit: usize,
    offset: usize,
    total: usize,
    counts: Vec<[usize; 4]>,
    records: Vec<Value>,
}

impl Page<'_> {
    fn add(&mut self, field: &str, bits: u8, make: impl FnOnce() -> Value) {
        if self.field.is_some_and(|wanted| wanted != field) {
            return;
        }
        let idx = INDEX[field];
        self.counts[idx][bits.trailing_zeros() as usize] += 1;
        if self.total >= self.offset && self.records.len() < self.limit {
            let mut record = make();
            record["field_id"] = json!(field);
            record["status"] = json!(status(bits));
            self.records.push(record);
        }
        self.total += 1;
    }
    fn add_source_row(
        &mut self,
        fields: &[(&str, u8)],
        load: impl FnOnce() -> Result<Value>,
        project: impl Fn(&str, &Value) -> Value,
    ) -> Result<()> {
        let matching = fields
            .iter()
            .filter(|(id, _)| self.field.is_none_or(|f| f == *id))
            .count();
        let row = if matching != 0
            && self.records.len() < self.limit
            && self.total.saturating_add(matching) > self.offset
        {
            load()?
        } else {
            Value::Null
        };
        for &(id, bits) in fields {
            self.add(id, bits, || project(id, &row));
        }
        Ok(())
    }
}

const DIRECT_RECORD: &str = "SELECT f.id,f.field_id,f.source_id,f.source_locator,f.value_json,f.unit,
    f.conditions_json,f.value_status,json_extract(f.metadata_json,'$.missing_reason') AS missing_reason,
    s.source_version_id,s.url AS source_url,
    (SELECT o.id FROM observations o WHERE o.id=f.id||':observation'
     AND o.material_id=f.material_id AND o.source_id=f.source_id AND o.source_locator=f.source_locator
     AND o.property=f.field_id) AS observation_id
    FROM catalog_facts f JOIN unified_sources s ON s.id=f.source_id WHERE f.id=?";

const OBSERVATION_RECORD: &str = "SELECT o.id,o.dataset_id,o.property,o.value,o.value_text,o.value_kind,
    o.structured_value_json,o.unit,o.module,o.declared_unit,o.basis,o.method,o.data_status,o.conditions_json,
    o.source_id,o.source_locator,o.property_id,o.source_url,o.source_version_id FROM unified_observations o WHERE o.id=?";

fn read_record(e: &Edition, id: &str, sql: &str) -> Result<Value> {
    query::rows(&e.db, sql, vec![id.to_owned().into()])?
        .pop()
        .with_context(|| format!("Missing evidence record: {id}"))
}

fn direct_facts(e: &Edition, material: &str, page: &mut Page<'_>) -> Result<()> {
    // Direct field facts precede legacy observation projections on an unfiltered page.
    let targeted = page.field.filter(|id| !FACT_METADATA.contains(id));
    let (clause, params) = filters(Some(material), targeted, "f.material_id", "f.field_id");
    let mut header = e.db.prepare(&format!(
        "SELECT f.id,f.field_id,f.value_status,{FACT_FLAGS}
        FROM catalog_facts f {clause} ORDER BY f.field_id,f.id"
    ))?;
    let mut rows = header.query(params_from_iter(&params))?;
    while let Some(row) = rows.next()? {
        let id = row.get_ref(0)?.as_str()?;
        let raw = row.get_ref(1)?.as_str()?;
        let key = FIELDS[*INDEX
            .get(raw)
            .with_context(|| format!("Invalid field in edition: {raw}"))?]
        .field_id;
        let mut keys = vec![];
        fact_fields(
            key,
            row.get(3)?,
            state(row.get_ref(2)?.as_str()?),
            |f, b| keys.push((f, b)),
        );
        page.add_source_row(
            &keys,
            || read_record(e, id, DIRECT_RECORD),
            |key, row| {
                let mut v = details("field_fact", row, fact_value(key, row));
                v["source_field_id"] = row["field_id"].clone();
                for name in [
                    "unit",
                    "conditions",
                    "value_status",
                    "missing_reason",
                    "observation_id",
                ] {
                    v[name] = row[name].clone();
                }
                v
            },
        )?;
    }

    Ok(())
}

fn relations(e: &Edition, material: &str, page: &mut Page<'_>) -> Result<()> {
    for (table, field_id, value_column, origin) in [
        (
            "material_links",
            "subject_relation",
            "l.target_id,l.relation",
            "material_link",
        ),
        (
            "material_citations",
            "source_document",
            "l.cited_source_id",
            "material_citation",
        ),
    ] {
        if page.field.is_some_and(|v| v != field_id) {
            continue;
        }
        let sql=format!("SELECT l.material_id AS id,l.source_id,l.source_locator,{value_column},
            s.source_version_id,s.url AS source_url FROM {table} l JOIN unified_sources s ON s.id=l.source_id
            WHERE l.material_id=? ORDER BY l.source_id,l.source_locator,{value_column}");
        for r in query::rows(&e.db, &sql, vec![material.to_owned().into()])? {
            page.add(field_id, PRESENT, || {
                let value = if origin == "material_link" {
                    json!({"from":material,"relation":r["relation"],"to":r["target_id"]})
                } else {
                    json!({"cited_source_id":r["cited_source_id"]})
                };
                details(origin, &r, value)
            });
        }
    }

    Ok(())
}

fn observations(e: &Edition, material: &str, page: &mut Page<'_>) -> Result<()> {
    let mut header = e.db.prepare(&format!(
        "SELECT o.id,o.dataset_id,o.property,o.data_status,{OBS_FLAGS}
        FROM observations o WHERE o.material_id=? AND {OBS_IS_PRIMARY} ORDER BY o.id"
    ))?;
    let mut rows = header.query([material])?;
    while let Some(row) = rows.next()? {
        let id = row.get_ref(0)?.as_str()?;
        let mut keys = vec![];
        observation_fields(
            row.get_ref(1)?.as_str()?,
            row.get_ref(2)?.as_str()?,
            row.get(4)?,
            state(row.get_ref(3)?.as_str()?),
            |f, b| keys.push((f, b)),
        );
        page.add_source_row(
            &keys,
            || read_record(e, id, OBSERVATION_RECORD),
            |key, row| {
                let mut v = details("observation", row, observation_value(key, row));
                v["observation_id"] = row["id"].clone();
                for name in [
                    "property",
                    "property_id",
                    "unit",
                    "module",
                    "declared_unit",
                    "method",
                    "basis",
                    "conditions",
                    "data_status",
                    "value_text",
                    "value_kind",
                ] {
                    v[name] = row[name].clone();
                }
                v
            },
        )?;
    }
    Ok(())
}

pub fn facts(
    e: &Edition,
    material: &str,
    field: Option<&str>,
    limit: usize,
    offset: usize,
) -> Result<Value> {
    let m = materials(e, Some(material), None)?
        .pop()
        .with_context(|| format!("Unknown material ID: {material}"))?;
    let mut page = Page {
        field,
        limit,
        offset,
        total: 0,
        counts: vec![[0; 4]; FIELDS.len()],
        records: vec![],
    };

    for (key, value) in material_values(&m, &e.id) {
        page.add(key, PRESENT, || details("material", &m, value));
    }
    direct_facts(e, material, &mut page)?;
    relations(e, material, &mut page)?;
    observations(e, material, &mut page)?;
    let mut fields = Vec::new();
    for (i, f) in FIELDS
        .iter()
        .enumerate()
        .filter(|(_, f)| field.is_none_or(|id| f.field_id == id))
    {
        let counts = page.counts[i];
        let mut bits = 0;
        for (index, count) in counts.iter().enumerate() {
            if *count > 0 {
                bits |= 1 << index;
            }
        }
        fields.push(json!({
            "field_id":f.field_id,"name_da":f.name_da,"group":f.group,"scope":f.scope,"status":status(bits),
            "record_count": counts.iter().sum::<usize>(), "reported":counts[0],"explicit_missing":counts[1],
            "not_applicable":counts[2], "conflicting":counts[3]
        }));
    }
    let next = offset.saturating_add(page.records.len());
    Ok(
        json!({"edition_id":e.id,"catalog_sha256":fingerprint(),"edition_catalog_sha256":e.manifest["inputs"]["catalog_sha256"],"material_id":material,"name":m["name"],
        "fields":fields,"records":page.records,"total_records":page.total,"limit":limit,"offset":offset,
        "next_offset":(next<page.total).then_some(next)}),
    )
}

pub fn coverage(
    e: &Edition,
    material: Option<&str>,
    dataset: Option<&str>,
    field: Option<&str>,
) -> Result<Value> {
    if let Some(id) = dataset {
        let exists: bool = e.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM datasets WHERE id=?)",
            [id],
            |r| r.get(0),
        )?;
        ensure!(exists, "Unknown dataset ID: {id}");
    }
    let mut subjects: HashMap<String, Vec<u8>> = HashMap::new();
    for m in materials(e, material, dataset)? {
        let mut states = vec![0; FIELDS.len()];
        for (key, _) in material_values(&m, &e.id) {
            states[INDEX[key]] |= PRESENT;
        }
        subjects.insert(m["id"].as_str().unwrap().to_owned(), states);
    }
    if let Some(m) = material {
        ensure!(
            subjects.contains_key(m),
            "Material ID outside selection: {m}"
        );
    }

    // One sequential pass per edition shard, or indexed material lookup when requested.
    // Decode no JSON for the millions of ordinary scalar results. Cache the projection
    // for repeats of the same field/status, e.g. EPD results with many modules.
    let (clause, params) = filters(material, dataset, "o.material_id", "o.dataset_id");
    let mut cache = HashMap::new();
    for schema in ["foundation", "extra"] {
        let condition = if clause.is_empty() { "WHERE" } else { "AND" };
        let sql = format!(
            "SELECT o.material_id,o.dataset_id,o.property,o.data_status,{OBS_FLAGS}
            FROM {schema}.observations o {clause} {condition} {OBS_IS_PRIMARY}"
        );
        let mut stmt = e.db.prepare(&sql)?;
        let mut rows = stmt.query(params_from_iter(&params))?;
        while let Some(r) = rows.next()? {
            let material = r.get_ref(0)?.as_str()?;
            let states = subjects
                .get_mut(material)
                .context("Observation with unknown material")?;
            let key: (String, String, i64, u8) = (
                r.get(1)?,
                r.get(2)?,
                r.get(4)?,
                state(r.get_ref(3)?.as_str()?),
            );
            let mapping = cache.entry(key).or_insert_with_key(|(ds, p, flags, s)| {
                let mut fields = vec![];
                observation_fields(ds, p, *flags, *s, |k, b| fields.push((INDEX[k], b)));
                fields
            });
            for &(i, b) in mapping.iter() {
                states[i] |= b;
            }
        }
    }
    // Supplementary evidence can cite a material in a different dataset. Selection
    // always follows that material, independently of which source supplied the fact.
    let (clause, params) = filters(material, None, "material_id", "");
    let sql = format!(
        "SELECT f.material_id,f.field_id,f.value_status,{FACT_FLAGS} FROM catalog_facts f {clause}"
    );
    let mut stmt = e.db.prepare(&sql)?;
    let mut rows = stmt.query(params_from_iter(&params))?;
    while let Some(r) = rows.next()? {
        if let Some(states) = subjects.get_mut(r.get_ref(0)?.as_str()?) {
            let key = r.get_ref(1)?.as_str()?;
            let field = FIELDS[*INDEX
                .get(key)
                .with_context(|| format!("Unknown field {key} in edition {}", e.id))?]
            .field_id;
            fact_fields(field, r.get(3)?, state(r.get_ref(2)?.as_str()?), |id, b| {
                states[INDEX[id]] |= b
            });
        }
    }
    for (table, key) in [
        ("material_links", "subject_relation"),
        ("material_citations", "source_document"),
    ] {
        let mut stmt = e.db.prepare(&format!(
            "SELECT DISTINCT material_id FROM {table} {clause}"
        ))?;
        let mut rows = stmt.query(params_from_iter(&params))?;
        while let Some(r) = rows.next()? {
            if let Some(states) = subjects.get_mut(r.get_ref(0)?.as_str()?) {
                states[INDEX[key]] |= PRESENT;
            }
        }
    }

    let total = subjects.len();
    let mut groups: BTreeMap<&str, [usize; 2]> = BTreeMap::new();
    let mut fields = vec![];
    for (i, f) in FIELDS
        .iter()
        .enumerate()
        .filter(|(_, f)| field.is_none_or(|x| f.field_id == x))
    {
        let mut count = [0; 5];
        for v in subjects.values().map(|s| s[i]) {
            for (j, flag) in [PRESENT, MISSING, INAPPLICABLE, CONFLICT]
                .iter()
                .enumerate()
            {
                count[j] += usize::from(v & flag != 0);
            }
            count[4] += usize::from(v == 0);
        }
        let g = groups.entry(f.group).or_default();
        g[0] += 1;
        g[1] += usize::from(count[0] > 0);
        fields.push(json!({"field_id":f.field_id,"name_da":f.name_da,"group":f.group,"scope":f.scope,
            "subjects_reported":count[0],"subjects_explicit_missing":count[1],"subjects_not_applicable":count[2],
            "subjects_conflicting":count[3],"subjects_not_recorded":count[4]}));
    }
    let groups: Vec<_> = groups
        .into_iter()
        .map(|(name, [total, reported])| {
            json!({"group":name,
        "field_count":total,"fields_with_reported_values":reported})
        })
        .collect();
    Ok(
        json!({"edition_id":e.id,"catalog_sha256":fingerprint(),"edition_catalog_sha256":e.manifest["inputs"]["catalog_sha256"],"material_id":material,"dataset":dataset,
        "subject_count":total,"field_count":fields.len(),"fields":fields,"groups":groups,
        "denominator":"All selected source records. Field applicability is specified in the dictionary. A subject can have both reported values and source markers for different observations."}),
    )
}
