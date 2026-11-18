use crate::store::{self, Edition};
use anyhow::{Context, Result, bail, ensure};
use rusqlite::{
    Connection, params_from_iter,
    types::{Value as Sql, ValueRef},
};
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::path::Path;

pub fn rows(db: &Connection, sql: &str, params: Vec<Sql>) -> Result<Vec<Value>> {
    let mut s = db.prepare(sql)?;
    let names = s.column_names().map(|n| n.to_string()).collect::<Vec<_>>();
    let mut rows = s.query(params_from_iter(params))?;
    let mut output = vec![];
    while let Some(r) = rows.next()? {
        let mut obj = json!({});
        for (i, key) in names.iter().enumerate() {
            if key == "search_text" {
                continue;
            }
            let value = match r.get_ref(i)? {
                ValueRef::Null => Value::Null,
                ValueRef::Integer(i) => i.into(),
                ValueRef::Real(f) => json!(f),
                ValueRef::Text(t) => {
                    let s = std::str::from_utf8(t)?;
                    if key.ends_with("_json") {
                        serde_json::from_str(s)?
                    } else {
                        s.into()
                    }
                }
                _ => bail!("Unexpected binary column {key}"),
            };
            obj[key.strip_suffix("_json").unwrap_or(key)] = value;
        }
        output.push(obj);
    }
    Ok(output)
}
#[derive(clap::Args)]
pub struct Page {
    #[arg(long,default_value_t=50,value_parser=clap::value_parser!(i64).range(1..=10000))]
    limit: i64,
    #[arg(long,default_value_t=0,value_parser=clap::value_parser!(i64).range(0..))]
    offset: i64,
}
impl Page {
    fn apply(&self, p: &mut Vec<Sql>) {
        p.extend([self.limit.into(), self.offset.into()]);
    }
}
#[derive(clap::Args)]
pub struct Search {
    #[arg(default_value = "")]
    query: String,
    #[arg(long)]
    family: Option<String>,
    #[arg(long)]
    kind: Option<String>,
    #[arg(long)]
    lineage: Option<String>,
    #[command(flatten)]
    page: Page,
}
pub fn search(e: &Edition, a: Search) -> Result<Value> {
    let vocab: Value = serde_json::from_str(include_str!("../data/unified/vocabulary.json"))?;
    let mut filters = vec![];
    let mut values = vec![];
    let q = store::fold(&a.query);
    for term in q.split_whitespace() {
        let mut ors = vec![];
        let mut terms = vec![term.to_string()];
        for (key, aliases) in vocab["search_aliases"].as_object().unwrap() {
            if store::fold(key) == term {
                for v in aliases.as_array().unwrap() {
                    terms.push(store::fold(v.as_str().unwrap()));
                }
            }
        }
        for t in terms {
            if t.chars().count() <= 2 {
                ors.push("instr(' '||replace(replace(replace(search_text,',',' '),'-',' '),'(',' ')||' ',?)>0");
                values.push(format!(" {t} ").into());
            } else {
                ors.push("instr(search_text,?)>0");
                values.push(t.into());
            }
        }
        for (family, aliases) in vocab["families"].as_object().unwrap() {
            if aliases
                .as_array()
                .unwrap()
                .iter()
                .any(|v| store::fold(v.as_str().unwrap()) == term)
            {
                ors.push("category=?");
                values.push(family.clone().into());
            }
        }
        filters.push(format!("({})", ors.join(" OR ")));
    }
    for (key, val) in [
        ("family_id", a.family),
        ("entity_kind", a.kind),
        ("lineage_id", a.lineage),
    ] {
        if let Some(v) = val {
            filters.push(format!("{key}=?"));
            values.push(v.into());
        }
    }
    if filters.is_empty() {
        filters.push("1".into());
    }
    a.page.apply(&mut values);
    let sql = format!(
        "SELECT id,name,dataset_id,entity_kind,family_id,lineage_id,source_version_id FROM unified_materials WHERE {} ORDER BY id LIMIT ? OFFSET ?",
        filters.join(" AND ")
    );
    Ok(json!({"snapshot":e.id,"materials":rows(&e.db,&sql,values)?}))
}
#[derive(clap::Args)]
pub struct Lookup {
    material: String,
    #[arg(long)]
    property: Option<String>,
    #[command(flatten)]
    page: Page,
}
pub fn lookup(e: &Edition, a: Lookup) -> Result<Value> {
    let m = rows(
        &e.db,
        "SELECT * FROM unified_materials WHERE id=?",
        vec![a.material.clone().into()],
    )?
    .into_iter()
    .next()
    .context("Unknown material ID")?;
    let mut clause = "material_id=?".to_owned();
    let mut p = vec![Sql::Text(a.material.clone())];
    if let Some(prop) = a.property {
        clause.push_str(" AND (property_id=? OR property=?)");
        p.extend([prop.clone().into(), prop.into()]);
    }
    let total: i64 = e.db.query_row(
        &format!("SELECT count(*) FROM unified_observations WHERE {clause}"),
        params_from_iter(&p),
        |r| r.get(0),
    )?;
    a.page.apply(&mut p);
    let obs = rows(
        &e.db,
        &format!("SELECT * FROM unified_observations WHERE {clause} ORDER BY id LIMIT ? OFFSET ?"),
        p,
    )?;
    let citations = rows(
        &e.db,
        "SELECT c.*,s.source_version_id,s.url FROM material_citations c JOIN unified_sources s ON s.id=c.cited_source_id WHERE c.material_id=? ORDER BY c.cited_source_id",
        vec![a.material.clone().into()],
    )?;
    let links = rows(
        &e.db,
        "SELECT * FROM material_links WHERE material_id=? OR target_id=? ORDER BY relation,target_id",
        vec![a.material.clone().into(), a.material.into()],
    )?;
    Ok(
        json!({"snapshot":e.id,"material":m,"total":total,"observations":obs,"links":links,"cited_sources":citations}),
    )
}
#[derive(clap::Args)]
pub struct Observations {
    #[arg(long)]
    property: String,
    #[arg(long)]
    dataset: Option<String>,
    #[arg(long)]
    module: Option<String>,
    #[arg(long)]
    unit: Option<String>,
    #[command(flatten)]
    page: Page,
}
pub fn observations(e: &Edition, a: Observations) -> Result<Value> {
    let mut filters = vec!["(property_id=? OR property=?)".to_owned()];
    let mut p = vec![a.property.clone().into(), a.property.into()];
    for (column, v) in [
        ("dataset_id", a.dataset),
        ("module", a.module),
        ("unit", a.unit),
    ] {
        if let Some(v) = v {
            filters.push(format!("{column}=?"));
            p.push(v.into());
        }
    }
    a.page.apply(&mut p);
    let sql = format!(
        "SELECT * FROM unified_observations WHERE {} ORDER BY dataset_id,id LIMIT ? OFFSET ?",
        filters.join(" AND ")
    );
    Ok(json!({"snapshot":e.id,"observations":rows(&e.db,&sql,p)?}))
}
pub fn properties(e: &Edition, page: Page) -> Result<Value> {
    let mut p = vec![];
    page.apply(&mut p);
    Ok(
        json!({"snapshot":e.id,"properties":rows(&e.db,"SELECT * FROM property_map ORDER BY property_id,dataset_id,raw_name LIMIT ? OFFSET ?",p)?}),
    )
}
pub fn changes(store: &Path, before: &str, after: &str, selection: Option<&Path>) -> Result<Value> {
    let a = store::open(store, before)?;
    let b = store::open(store, after)?;
    fn versions(e: &Edition) -> Result<BTreeMap<String, String>> {
        let mut st =
            e.db.prepare("SELECT id,source_version_id FROM unified_sources")?;
        Ok(st
            .query_map([], |r| Ok((r.get(0)?, r.get(1)?)))?
            .collect::<rusqlite::Result<_>>()?)
    }
    let old = versions(&a)?;
    let new = versions(&b)?;
    let mut changed = BTreeMap::new();
    for k in old.keys().chain(new.keys()) {
        if old.get(k) != new.get(k) {
            changed.insert(k, json!({"id":k,"before":old.get(k),"after":new.get(k)}));
        }
    }
    let mut result =
        json!({"before":a.id,"after":b.id,"sources":changed.values().collect::<Vec<_>>()});
    if let Some(path) = selection {
        let sel = store::read(path)?;
        ensure!(
            sel["snapshot"] == a.id,
            "Selection does not belong to before edition"
        );
        let mut affected = vec![];
        for (part, choice_name) in sel["parts"]
            .as_object()
            .context("Invalid selection parts")?
        {
            let choice = &sel["materials"][choice_name.as_str().context("Invalid part mapping")?];
            let climate = choice["gwp_observation_ids"]
                .as_array()
                .into_iter()
                .flatten();
            for obs in std::iter::once(&choice["density_observation_id"]).chain(climate) {
                let p = vec![
                    obs.as_str()
                        .context("Missing observation ID")?
                        .to_owned()
                        .into(),
                    store::text(choice, "material_id")?.to_owned().into(),
                ];
                let sql = "SELECT property_id,source_version_id,metadata_json FROM unified_observations WHERE id=? AND material_id=?";
                let earlier = rows(&a.db, sql, p.clone())?;
                ensure!(
                    earlier.len() == 1,
                    "Observation missing from selection's edition"
                );
                let later = rows(&b.db, sql, p)?;
                if earlier != later {
                    affected.push(json!({"part":part,"observation_id":obs,"change":if later.is_empty(){"absent"}else{"changed"}}));
                }
            }
        }
        result["affected_selections"] = affected.into();
    }
    Ok(result)
}
