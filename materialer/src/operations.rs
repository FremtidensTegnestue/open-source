//! Pin individual operating instructions and EPD scenarios to the applicable component.
#[path = "operations/lincrete.rs"]
mod lincrete;
use anyhow::{Context, Result, ensure};
use clap::Args as ClapArgs;
use regex::Regex;
use reqwest::blocking::Client;
use serde::Deserialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    io::{Read, Write},
    path::{Path, PathBuf},
    time::Duration,
};
use tempfile::NamedTempFile;
use zip::ZipArchive;

const PUBLIC: &str = "data/supplements/operations";
const LOCAL: &str = "data/staging/operations-dk";

#[derive(Debug, ClapArgs)]
pub struct Args {
    #[arg(skip)]
    pub root: PathBuf,
    /// Rebuild the Danish EPD and manufacturer-manual overlay, used together with epd-danmark.
    #[arg(long)]
    pub danish: bool,
    /// Write the generated bundle files here.
    #[arg(long)]
    pub output: Option<PathBuf>,
    /// Use only the archived bytes already present on this computer or in the public supplement.
    #[arg(long)]
    pub offline: bool,
}

#[derive(Deserialize)]
struct Entry {
    kind: String,
    material_id: String,
    component: String,
    source: Value,
    page: Option<u32>,
    pointer: Option<String>,
}

fn required<'a>(o: &'a Value, k: &str) -> Result<&'a str> {
    o[k].as_str().with_context(|| format!("Missing {k}"))
}

fn hash(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn original(root: &Path, entry: &Entry, client: &Client, offline: bool) -> Result<Vec<u8>> {
    let source = &entry.source;
    let path = root.join(required(source, "local_path")?);
    let existing = path.is_file();
    let bytes = if existing {
        fs::read(&path)?
    } else if entry.pointer.is_some() {
        let mut archive = ZipArchive::new(fs::File::open(
            root.join(PUBLIC).join("oekobaudat-originals.zip"),
        )?)?;
        let mut output = Vec::new();
        archive
            .by_name(
                path.file_name()
                    .and_then(|v| v.to_str())
                    .context("Missing archive filename")?,
            )?
            .read_to_end(&mut output)?;
        output
    } else {
        ensure!(
            !offline,
            "Missing original in offline mode: {}",
            path.display()
        );
        client
            .get(required(source, "url")?)
            .send()?
            .error_for_status()?
            .bytes()?
            .to_vec()
    };
    ensure!(
        hash(&bytes) == required(source, "sha256")?,
        "Original checksum mismatch for {}",
        path.display()
    );
    if !existing {
        fs::create_dir_all(path.parent().context("Missing source directory")?)?;
        write_file(&path, &bytes)?;
    }
    Ok(bytes)
}

fn write_file(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut tmp = NamedTempFile::new_in(path.parent().context("Missing directory")?)?;
    tmp.write_all(bytes)?;
    tmp.persist(path)?;
    Ok(())
}

// The normalized text is only used as a matching surface; the cited original retains its typography.
fn compact(s: &str) -> String {
    s.chars()
        .filter(|c| !c.is_whitespace() && *c != '\u{ad}')
        .flat_map(char::to_lowercase)
        .collect()
}

fn amount(text: &str, pattern: &str) -> Result<Value> {
    let regex = Regex::new(pattern)?;
    let value = regex
        .captures(text)
        .with_context(|| format!("Missing numeric evidence for {pattern}"))?
        .get(1)
        .context("Missing numeric capture")?
        .as_str();
    Ok(serde_json::from_str(&value.replace(',', "."))?)
}

fn confirm(text: &str, anchor: &str) -> Result<()> {
    ensure!(
        text.contains(&compact(anchor)),
        "Missing evidence anchor {anchor:?}"
    );
    Ok(())
}

struct Facts<'a> {
    entry: &'a Entry,
    rows: Vec<Value>,
}

impl Facts<'_> {
    fn put(
        &mut self,
        field: &str,
        value: Value,
        unit: Option<&str>,
        locator: &str,
        conditions: &Value,
    ) {
        let key = format!(
            "{}\n{}\n{}\n{}\n{}",
            self.entry.material_id,
            self.entry.source["id"],
            locator,
            conditions["statement_group"],
            field
        );
        let status =
            if field == "maintenance_frequency" && conditions.get("conflict_group").is_some() {
                "conflicting"
            } else {
                "reported"
            };
        self.rows.push(json!({
            "id":format!("operations:fact:{}", &hash(key.as_bytes())[..32]),"material_id":self.entry.material_id,
            "field_id":field,"value":value,"unit":unit,"value_status":status,
            "source_id":self.entry.source["id"],"source_locator":locator,"conditions":conditions
        }));
    }

    fn life(&mut self, value: Value, locator: &str, conditions: &Value) {
        self.put(
            "service_life_type",
            json!("reference_service_life"),
            None,
            locator,
            conditions,
        );
        self.put(
            "service_life_value",
            value,
            Some("years"),
            locator,
            conditions,
        );
    }

    fn task(&mut self, action: &str, locator: &str, conditions: &Value) {
        self.put(
            "maintenance_action",
            json!(action),
            None,
            locator,
            conditions,
        );
        self.put(
            "maintenance_basis",
            conditions["basis"].clone(),
            None,
            locator,
            conditions,
        );
    }

    fn scheduled(
        &mut self,
        action: &str,
        number: Value,
        unit: &str,
        locator: &str,
        conditions: &Value,
    ) {
        self.task(action, locator, conditions);
        self.put(
            "maintenance_frequency",
            number,
            Some(unit),
            locator,
            conditions,
        );
    }
}

fn conditions(group: &str, component: &str, basis: &str) -> Value {
    json!({"statement_group":group,"component":component,"basis":basis})
}
const SCENARIO: &str = "epd_scenario";
const MANUAL: &str = "manufacturer_maintenance_instruction";

fn from_json(facts: &mut Facts, bytes: &[u8]) -> Result<()> {
    let entry = facts.entry;
    let pointer = entry
        .pointer
        .as_deref()
        .context("Missing evidence pointer")?;
    let doc: Value = serde_json::from_slice(bytes)?;
    let source = doc
        .pointer(pointer)
        .and_then(Value::as_str)
        .context("Original passage absent")?;
    let text = compact(source);
    let mut c = conditions("reference-life", &entry.component, SCENARIO);
    match entry.kind.as_str() {
        "pipe" | "json_rsl" => {
            let value = amount(&text, r"referenceservicelife(?:\(rsl\))?of([0-9]+)years")?;
            if entry.kind == "pipe" {
                confirm(&text, "replacement of sanitary and heating piping")?;
                c["application"] = json!("insulation of heating and sanitary installations");
                facts.put(
                    "end_of_service_criterion",
                    json!("planned replacement of the pipe and recycling of the insulation"),
                    None,
                    pointer,
                    &c,
                );
            } else if text.contains("mountedon") {
                let finish = if text.contains("unpaintedfinish") {
                    "unpainted"
                } else {
                    confirm(&text, "painted finish")?;
                    "painted"
                };
                confirm(&text, "ceiling")?;
                c["mounting"] = json!("ceiling");
                c["finish"] = json!(finish);
                facts.put(
                    "service_exposure",
                    json!({"mounting":"ceiling","finish":finish}),
                    None,
                    pointer,
                    &c,
                );
            } else {
                confirm(&text, "wall with Cedral sidings")?;
                c["application"] = json!("wall cladding");
            }
            facts.life(value, pointer, &c);
        }
        "cork" => {
            for (group, action, anchor, number, unit) in [
                (
                    "vacuum",
                    "vacuum",
                    "vacuum cleaning once a week",
                    1,
                    "times/week",
                ),
                (
                    "wet-clean",
                    "wet clean",
                    "wet cleaning twice a year",
                    2,
                    "times/year",
                ),
            ] {
                confirm(&text, anchor)?;
                let mut c = conditions(group, &entry.component, SCENARIO);
                c["module"] = json!("B2");
                facts.scheduled(action, json!(number), unit, pointer, &c);
            }
        }
        "tiles" => {
            let n = amount(&text, r"walltilescleaned([0-9]+)timesayear")?;
            let mut c = conditions("wall-tile-cleaning", "wall tiles", SCENARIO);
            c["module"] = json!("B2");
            c["reference_area_m2"] = json!(1);
            facts.scheduled("clean", n, "times/year", pointer, &c);
        }
        "carpet" => {
            confirm(&text, "carpet cleaning per year, including vacuuming")?;
            confirm(&text, "hot water cleaning")?;
            // The annual reporting period does not give the number of cleaning visits.
            for (group, action) in [("vacuum", "vacuum"), ("hot-water", "clean with hot water")] {
                let mut c = conditions(group, &entry.component, SCENARIO);
                c["module"] = json!("B2");
                c["reporting_period_years"] = json!(1);
                facts.task(action, pointer, &c);
            }
        }
        "rockpanel" => {
            let base = amount(&text, r"requiresre-coatingafter([0-9]+)years")?;
            let plus = amount(
                &text,
                r"protectpluscoatingrequiresmaintenanceintervalsevery([0-9]+)years",
            )?;
            let mut c = conditions(
                "waterborne-finish-first",
                "Rockpanel Durable waterborne coating",
                SCENARIO,
            );
            c["dataset_valid_until"] = json!(2025);
            facts.task("recoat", pointer, &c);
            facts.put("first_due", base, Some("years"), pointer, &c);
            let mut c = conditions("protectplus-interval", "ProtectPlus coating", SCENARIO);
            c["dataset_valid_until"] = json!(2025);
            facts.scheduled("maintain coating", plus, "years/interval", pointer, &c);
        }
        "lincrete_c1" => {
            let value = amount(&text, r"demontagederlincrete-paneelenach([0-9]+)jahren")?;
            let mut c = conditions("dismantling-C1", "LinCrete facade panel", SCENARIO);
            c["module"] = json!("C1");
            c["timing_years"] = value;
            facts.put(
                "end_of_service_criterion",
                json!("dismantling of the facade panel in the C1 scenario"),
                None,
                pointer,
                &c,
            );
        }
        other => anyhow::bail!("Unknown JSON recipe {other}"),
    }
    Ok(())
}

fn pdf_text(doc: &pdf_extract::Document, page: u32) -> Result<String> {
    Ok(compact(
        &crate::danish::document_page_lines(doc, page)?.join("\n"),
    ))
}
fn place(page: u32, section: &str) -> String {
    format!("PDF page {page}, {section}")
}

fn from_pdf(facts: &mut Facts, bytes: &[u8]) -> Result<()> {
    let entry = facts.entry;
    let mut doc = pdf_extract::Document::load_mem(bytes)?;
    if doc.is_encrypted() {
        doc.decrypt("")?;
    }
    let kind = entry.kind.as_str();
    if matches!(kind, "dg_manual" | "fd_manual") {
        return manual(facts, &doc, kind == "dg_manual");
    }
    if kind == "lincrete_pdf" {
        return lincrete::extract(facts, &doc);
    }
    let page = entry.page.context("Missing RSL page")?;
    let text = pdf_text(&doc, page)?;
    if kind == "swisspearl" {
        let c = conditions(
            "reference-life",
            "1 m² Swisspearl fibre-cement panel",
            SCENARIO,
        );
        let value = amount(&text, r"referenceservicelifeof([0-9]+)years/product")?;
        facts.life(
            value,
            &place(page, "LCA interpretation, reference product"),
            &c,
        );
        return Ok(());
    }
    if kind == "triplan" {
        let mut c = conditions("reference-life", "polyethylene mat", SCENARIO);
        c["method"] = json!("BUILD 2021:32, Annex 4 as cited by the EPD");
        let value = amount(&text, r"servicelifeof([0-9]+)yearscf")?;
        let loc = place(page, "Reference Service Life (RSL), polyethylene mat");
        facts.life(value, &loc, &c);
        confirm(&text, "occur post de-construction/ demolition of the")?;
        c["statement_group"] = json!("installed-on-steel-profile");
        facts.put(
            "end_of_service_criterion",
            json!("mat retained until the steel profile is dismantled or demolished"),
            None,
            &loc,
            &c,
        );
        return Ok(());
    }
    let rsl_table = place(page, "Reference service life, RSL information");
    let rsl_pattern = if kind == "product_roof_rsl" {
        r"yearsforbuilding,([0-9]+)yearsforproduct"
    } else {
        r"referenceservicelife([0-9]+)years"
    };
    let years = amount(&text, rsl_pattern).or_else(|_| {
        amount(
            &text,
            r"rslinformationunit([0-9]+)referenceservicelifeyears",
        )
    })?;
    let c = conditions("reference-life", &entry.component, SCENARIO);
    facts.life(years, &rsl_table, &c);
    if matches!(kind, "door" | "window") {
        let parts = if kind == "door" {
            [
                ("clean", "door system", r"cleaning([0-9]+)timesayear"),
                ("lubricate", "door system", r"lubricated([0-9]+)timeayear"),
            ]
        } else {
            [
                ("clean", "window", r"washing([0-9]+)timesayear"),
                ("lubricate", "window", r"lubricating([0-9]+)timeayear"),
            ]
        };
        for (action, component, pattern) in parts {
            let c = conditions(action, component, SCENARIO);
            facts.scheduled(
                action,
                amount(&text, pattern)?,
                "times/year",
                &rsl_table,
                &c,
            );
        }
        if kind == "door" {
            let c = conditions("lubricate", "door system", SCENARIO);
            let value = amount(
                &text,
                r"lubricant\(permaintenancecycle\)([0-9]+[.,][0-9]+)g/m",
            )?;
            facts.put(
                "resources_per_action",
                json!({"resource":"lubricant","amount":value}),
                Some("g/m²/cycle"),
                &place(page, "B2 Maintenance, Lubricant (per maintenance cycle)"),
                &c,
            );
        }
    } else if kind == "rv2" {
        confirm(&text, "replacement of filters once a year")?;
        confirm(&text, "/year and a half")?;
        confirm(
            &pdf_text(&doc, 2)?,
            "every year and a half instead of every year",
        )?;
        for (group, period, unit, section) in [
            (
                "filter-RSL-table",
                1,
                "times/year",
                "Reference service life, Maintenance",
            ),
            (
                "filter-B2-revision",
                18,
                "months/interval",
                "Use (B1–B7), B2 Maintenance cycle; revision note on PDF page 2",
            ),
        ] {
            let mut c = conditions(group, "PET filter", SCENARIO);
            c["conflict_group"] = json!("RV2 filter replacement interval");
            c["conflict_note"] = json!("RSL table and revised B2 scenario differ");
            if period == 18 {
                c["reported_period"] = json!("one year and a half");
            }
            facts.scheduled(
                "replace filter",
                json!(period),
                unit,
                &place(page, section),
                &c,
            );
        }
    } else if kind == "hemp" {
        confirm(&text, "no maintenance needed")?;
        let c = conditions("maintenance-assumption", &entry.component, SCENARIO);
        facts.task("no maintenance assumed in the EPD", &rsl_table, &c);
    } else {
        ensure!(
            matches!(kind, "rsl" | "product_roof_rsl"),
            "Unknown Danish recipe {kind}"
        );
    }
    Ok(())
}

fn manual(facts: &mut Facts, doc: &pdf_extract::Document, dg: bool) -> Result<()> {
    let text = pdf_text(doc, 3)?;
    confirm(&text, "door handles")?;
    let loc = place(3, "Fittings, 1. Hinges");
    let c = conditions("manual-lubricate", "hinges", MANUAL);
    facts.task("lubricate", &loc, &c);
    if dg {
        confirm(&text, "as required")?;
        confirm(&text, "if adjusting height")?;
        facts.put(
            "condition_trigger",
            json!(["as required", "when adjusting hinge height"]),
            None,
            &loc,
            &c,
        );
    } else {
        confirm(&text, "if required")?;
        facts.put("condition_trigger", json!("as required"), None, &loc, &c);
    }
    let loc = place(3, "Fittings, 2. Door handles");
    let c = conditions("manual-handles", "door handles", MANUAL);
    confirm(&text, "depending on the amount of use")?;
    facts.task("inspect function and attachment", &loc, &c);
    facts.put(
        "maintenance_frequency",
        json!({"frequency":"regular","depends_on":"amount of use"}),
        None,
        &loc,
        &c,
    );
    let text = pdf_text(doc, 2)?;
    confirm(&text, "mild")?;
    confirm(&text, "rubber seals")?;
    let loc = place(2, "Materials, 3. Rubber seals");
    let c = conditions("manual-seals", "rubber seals", MANUAL);
    facts.task("clean", &loc, &c);
    facts.put(
        "maintenance_procedure",
        json!(
            "Wipe with a cloth wrung out in water with mild detergent. Avoid petroleum products."
        ),
        None,
        &loc,
        &c,
    );
    let loc = place(2, "Materials, 1. Frame");
    let c = conditions("manual-frame", "aluminium frame profiles", MANUAL);
    confirm(&text, "liquid concrete or")?;
    facts.task("clean immediately", &loc, &c);
    facts.put(
        "condition_trigger",
        json!("contact with wet concrete or mortar"),
        None,
        &loc,
        &c,
    );
    Ok(())
}

pub fn run(args: Args) -> Result<Value> {
    let snapshot = if args.danish {
        "danish.lock.json"
    } else {
        "public.lock.json"
    };
    let dataset = if args.danish {
        "operations-dk"
    } else {
        "operations"
    };
    let recipes: Vec<Entry> =
        serde_json::from_slice(&fs::read(args.root.join(PUBLIC).join(snapshot))?)?;
    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .user_agent("ft-materials source-bound collector")
        .build()?;
    let mut sources = BTreeMap::new();
    let mut rows = Vec::new();
    let mut affected = BTreeSet::new();
    for entry in &recipes {
        let result = (|| -> Result<Vec<Value>> {
            let bytes = original(&args.root, entry, &client, args.offline)?;
            let mut facts = Facts {
                entry,
                rows: Vec::new(),
            };
            if entry.pointer.is_some() {
                from_json(&mut facts, &bytes)?;
            } else {
                from_pdf(&mut facts, &bytes)?;
            }
            Ok(facts.rows)
        })()
        .with_context(|| {
            format!(
                "Reading {} ({})",
                entry.source["title"], entry.source["url"]
            )
        })?;
        rows.extend(result);
        affected.insert(&entry.material_id);
        let id = required(&entry.source, "id")?;
        if id.starts_with("operations:source:") {
            sources.insert(id, &entry.source);
        }
    }
    rows.sort_by(|a, b| a["id"].as_str().cmp(&b["id"].as_str()));
    ensure!(
        rows.windows(2).all(|p| p[0]["id"] != p[1]["id"]),
        "Duplicate fact ID"
    );
    let mut field_counts = BTreeMap::<&str, usize>::new();
    for fact in &rows {
        *field_counts.entry(required(fact, "field_id")?).or_default() += 1;
    }
    let summary = json!({"dataset":dataset,"facts":rows.len(),"sources":sources.len(),"materials":0,"observations":0,
        "source_documents":recipes.len(),"affected_materials":affected.len(),"field_counts":field_counts,
        "depends_on":if args.danish {"epd-danmark"}else{"environmental"}});
    let output = args
        .output
        .unwrap_or_else(|| args.root.join(if args.danish { LOCAL } else { PUBLIC }));
    fs::create_dir_all(&output)?;
    for (name, items) in [
        ("sources", sources.values().copied().collect::<Vec<_>>()),
        ("materials", vec![]),
        ("observations", vec![]),
        ("facts", rows.iter().collect()),
    ] {
        let mut bytes = Vec::new();
        for item in items {
            serde_json::to_writer(&mut bytes, item)?;
            bytes.push(b'\n');
        }
        write_file(&output.join(format!("{name}.jsonl")), &bytes)?;
    }
    let mut bytes = serde_json::to_vec_pretty(&summary)?;
    bytes.push(b'\n');
    write_file(&output.join("summary.json"), &bytes)?;
    Ok(summary)
}
