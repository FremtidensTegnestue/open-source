//! Collect EPD Danmark's source register and extract declared EN 15804+A2 results.
#[path = "danish/fresh.rs"]
mod fresh;
#[path = "danish/pdf.rs"]
mod pdf;
use anyhow::{Context, Result, bail, ensure};
use chrono::Utc;
use clap::Args as ClapArgs;
use flate2::read::GzDecoder;
use regex::Regex;
use reqwest::{Url, blocking::Client};
use serde::Deserialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    io::{Cursor, Read, Write},
    path::{Path, PathBuf},
    time::Duration,
};
use tempfile::NamedTempFile;

const INDEX: &str = "https://www.epddanmark.dk/epd-databasen/";
const GPI: &str = "https://www.epddanmark.dk/media/ifrh2ghc/general-programme-instructions_v3.pdf";
const RAW: &str = "data/raw/epd-danmark/objects";
const PUBLIC: &str = "data/supplements/epd-danmark";
const LICENSE: &str = "EPD Danmark GPI v3 §5.9: EPD owners retain ownership. Bulk redistribution grant not identified.";

#[derive(Debug, ClapArgs)]
pub struct Args {
    #[arg(skip)]
    pub root: PathBuf,
    /// Rebuild a checksum-pinned source edition (default).
    #[arg(long, conflicts_with = "refresh")]
    pub locked: bool,
    /// Retrieve the current publisher listings and create a new immutable source lock.
    #[arg(long)]
    pub refresh: bool,
    #[arg(long)]
    pub lock: Option<PathBuf>,
    /// Normalized bundle directory; refreshed editions should use a new directory.
    #[arg(long)]
    pub output: Option<PathBuf>,
}
fn sha(s: &[u8]) -> String {
    hex::encode(Sha256::digest(s))
}
fn sid(url: &str) -> String {
    format!("epd-danmark:source:{}", sha(url.as_bytes()))
}
fn json_bytes(v: &Value) -> Result<Vec<u8>> {
    let mut b = serde_json::to_vec(v)?;
    b.push(b'\n');
    Ok(b)
}
fn write_new(path: &Path, data: &[u8]) -> Result<()> {
    let parent = path.parent().context("missing parent directory")?;
    fs::create_dir_all(parent)?;
    let mut temp = NamedTempFile::new_in(parent)?;
    temp.write_all(data)?;
    temp.flush()?;
    match temp.persist_noclobber(path) {
        Ok(_) => Ok(()),
        Err(_) if path.is_file() && fs::read(path)? == data => Ok(()),
        Err(e) => Err(e.error.into()),
    }
}
#[derive(Deserialize)]
struct Layouts {
    known: BTreeMap<String, Value>,
    recipes: BTreeMap<String, pdf::Recipe>,
}
struct Originals {
    root: PathBuf,
    client: Client,
    expected: Option<BTreeMap<String, Value>>,
    seen: BTreeMap<String, Value>,
}
impl Originals {
    fn local(&self, info: &Value) -> Result<PathBuf> {
        let h = info["sha256"].as_str().context("missing original hash")?;
        let ext = info["extension"].as_str().context("missing format")?;
        ensure!(
            h.len() == 64
                && h.bytes().all(|c| c.is_ascii_hexdigit())
                && matches!(ext, "html" | "pdf" | "zip"),
            "Invalid source object"
        );
        Ok(self.root.join(RAW).join(format!("{h}.{ext}")))
    }
    fn fetch(&mut self, url: &str, ext: &str) -> Result<PathBuf> {
        let url = publisher_url(url)?;
        if let Some(item) = self.seen.get(&url) {
            return self.local(item);
        }
        let expected = self
            .expected
            .as_ref()
            .map(|map| {
                map.get(&url)
                    .with_context(|| format!("Source absent in lock: {url}"))
            })
            .transpose()?
            .cloned();
        if let Some(item) = &expected {
            ensure!(
                item["extension"] == ext,
                "Original media type in lock differs for {url}"
            );
            let p = self.local(item)?;
            if let Ok(content) = fs::read(&p) {
                ensure!(
                    item["sha256"] == sha(&content),
                    "Local original failed checksum: {}",
                    p.display()
                );
                self.seen.insert(url, item.clone());
                return Ok(p);
            }
        }
        let mut last = None;
        let mut bytes = None;
        for pass in 0..3 {
            match self
                .client
                .get(&url)
                .send()
                .and_then(|r| r.error_for_status())
                .and_then(|r| r.bytes())
            {
                Ok(body) => {
                    bytes = Some(body);
                    break;
                }
                Err(e) => {
                    last = Some(e);
                    if pass < 2 {
                        std::thread::sleep(Duration::from_millis(250 * (pass + 1)));
                    }
                }
            }
        }
        let bytes = match bytes {
            Some(bytes) => bytes,
            None => {
                return Err(last.context("No publisher response")?)
                    .with_context(|| format!("Downloading {url}"));
            }
        };
        ensure!(
            ext != "pdf" || bytes.starts_with(b"%PDF-"),
            "Invalid PDF at {url}"
        );
        let digest = sha(&bytes);
        let info = if let Some(item) = expected {
            ensure!(
                item["sha256"] == digest,
                "Publisher changed locked source {url}"
            );
            item
        } else {
            json!({"sha256":digest,"retrieved_at":Utc::now().to_rfc3339(),"extension":ext,"bytes":bytes.len()})
        };
        let p = self.local(&info)?;
        write_new(&p, &bytes)?;
        self.seen.insert(url, info);
        Ok(p)
    }
}
fn publisher_url(href: &str) -> Result<String> {
    let b = Url::parse(INDEX)?;
    let u = b.join(&html_escape::decode_html_entities(href))?;
    ensure!(
        u.scheme() == "https" && u.host_str() == Some("www.epddanmark.dk"),
        "Unexpected publisher link"
    );
    Ok(u.to_string())
}
fn clean(s: &str) -> String {
    use std::sync::LazyLock;
    static TAG: LazyLock<Regex> = LazyLock::new(|| Regex::new("<[^>]+>").unwrap());
    html_escape::decode_html_entities(&TAG.replace_all(s, " "))
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}
struct Entry {
    name: String,
    detail: String,
    pdfs: Vec<String>,
}
fn parse_index(s: &str) -> Result<(Vec<Entry>, Option<String>)> {
    let group = Regex::new(r"\bdiv-table-row\s+searchItem\b")?;
    let title = Regex::new(r#"(?is)<h3>\s*<a\b[^>]+href="([^"]+)"[^>]*>(.*?)</a>"#)?;
    let pdf = Regex::new(r#"(?is)<a\b[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>"#)?;
    let primary = Regex::new(r"(?i)^EPD Fil\s*\(EN\s*15804\s*\+\s*A2\)$")?;
    let bulk = Regex::new(r#"(?i)href="([^"]+\.zip)"[^>]*>\s*HER"#)?
        .captures(s)
        .map(|m| publisher_url(&m[1]))
        .transpose()?;
    let mut entries = Vec::new();
    for chunk in group.split(s).skip(1) {
        let h = title
            .captures(chunk)
            .context("Publisher listing lacks heading")?;
        let mut urls = Vec::new();
        for m in pdf.captures_iter(chunk) {
            if primary.is_match(&clean(&m[2])) {
                urls.push(publisher_url(&m[1])?);
            }
        }
        urls.sort();
        urls.dedup();
        entries.push(Entry {
            name: clean(&h[2]),
            detail: publisher_url(&h[1])?,
            pdfs: urls,
        });
    }
    ensure!(
        !entries.is_empty(),
        "Publisher index has no recognizable declarations"
    );
    Ok((entries, bulk))
}
fn detail(s: &str) -> BTreeMap<String, String> {
    use std::sync::LazyLock;
    static ROW: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r"(?is)<strong>(.*?)</strong>\s*</div>\s*<div[^>]+>(.*?)</div>").unwrap()
    });
    ROW.captures_iter(s)
        .map(|c| (clean(&c[1]).trim_end_matches(':').into(), clean(&c[2])))
        .collect()
}
fn reference(s: &str) -> Option<(f64, String)> {
    use std::sync::LazyLock;
    static REF: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r"(?i)^([0-9]+(?:[.,][0-9]+)?)\s*(m[23²³]?|kg|t|stk\.?|piece|pcs\.?)$").unwrap()
    });
    static AMBIGUOUS: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"^[1-9]\d{0,2}[.,]\d{3}$").unwrap());
    let m = REF.captures(s.trim())?;
    if AMBIGUOUS.is_match(&m[1]) {
        return None;
    }
    let a: f64 = m[1].replace(',', ".").parse().ok()?;
    if !a.is_finite() || a <= 0.0 {
        return None;
    }
    let u = m[2]
        .to_lowercase()
        .trim_end_matches('.')
        .replace('²', "2")
        .replace('³', "3");
    Some((
        a,
        if matches!(u.as_str(), "piece" | "pcs") {
            "stk".into()
        } else {
            u
        },
    ))
}
fn result_property(indicator: &str) -> (String, &'static str) {
    let climate = match indicator {
        "gwp-bio" | "gwp-biogenic" => Some("gwp_biogenic"),
        "gwp-total" => Some("gwp_total"),
        "gwp-fossil" => Some("gwp_fossil"),
        "gwp-luluc" => Some("gwp_luluc"),
        _ => None,
    };
    if let Some(p) = climate {
        return (p.into(), "kg CO2-eq");
    }
    let unit = match indicator {
        "pere" | "perm" | "pert" | "penre" | "penrm" | "penrt" | "rsf" | "nrsf" | "eee" | "eet"
        | "adpf" => "MJ",
        "sm" | "hwd" | "nhwd" | "rwd" | "cru" | "mfr" | "mer" => "kg",
        "fw" => "m3",
        "odp" => "kg CFC-11 eq",
        "ep-freshwater" => "kg P eq",
        "ep-marine" => "kg N eq",
        "pocp" => "kg NMVOC eq",
        "adpm" => "kg Sb eq",
        "ep-terrestrial" => "mol N eq",
        "etp-fw" => "CTUe",
        "htp-c" | "htp-nc" => "CTUh",
        _ => "",
    };
    (
        format!("epd_indicator_{}", indicator.replace('-', "_")),
        unit,
    )
}
#[derive(Default)]
struct Product {
    material: Option<Value>,
    obs: Vec<Value>,
    status: String,
}
impl Product {
    fn excluded(reason: &str) -> Self {
        Self {
            status: reason.into(),
            ..Self::default()
        }
    }
}
struct ResultRow {
    page: u32,
    line: usize,
    header: usize,
    indicator: String,
    unit: String,
    modules: Vec<String>,
    cells: Vec<String>,
}
fn result(
    material: Value,
    ref_text: &str,
    loc: &str,
    rows: Vec<ResultRow>,
    locator_style: &str,
) -> Result<Product> {
    let (amount, ref_unit) =
        reference(ref_text).context("Unsupported declared amount in source recipe")?;
    let mut obs = Vec::new();
    for row in rows {
        let (prop, unit) = result_property(&row.indicator);
        ensure!(!unit.is_empty(), "Unknown source indicator");
        ensure!(
            row.modules.len() == row.cells.len(),
            "Incomplete result row"
        );
        for (module, value_text) in row.modules.iter().zip(row.cells) {
            let val = match value_text.as_str() {
                "ND" | "MND" | "MNR" | "NPD" | "INA" => None,
                _ => {
                    let v: f64 = value_text.replace(',', ".").parse()?;
                    ensure!(v.is_finite(), "Nonfinite source result");
                    Some(v)
                }
            };
            let m = material["id"].as_str().context("material id")?;
            obs.push(json!({"id":format!("{m}:{prop}:{module}"),"material_id":m,"property":prop,"value":val,"value_text":value_text,
                "unit":unit,"declared_unit":material["declared_unit"],"module":module,
                "basis":"Publisher-declared EPD result; individual module or published combined module","method":"EN 15804+A2",
                "data_status":if val.is_some(){"reported"}else{"source_marker"},"source_id":material["source_id"],
                "source_locator":format!("PDF page {} {locator_style} line {}; {} column {} (header line {})",row.page,row.line,row.indicator,module,row.header),
                "conditions":{"indicator":row.indicator,"original_result_unit":row.unit,"declared_amount":amount,"declared_unit":ref_unit,"original_reference":ref_text,
                    "pdf_reference_locator":loc,"detail_source_id":material["detail_source_id"],"declaration":material["declaration"]}}));
        }
    }
    Ok(Product {
        material: Some(material),
        obs,
        status: "imported".into(),
    })
}
fn source(url: &str, info: &Value) -> Result<Value> {
    let u = Url::parse(url)?;
    let p = u.path();
    let fname = p.rsplit('/').next().filter(|s| !s.is_empty()).unwrap_or(p);
    let ext = info["extension"].as_str().context("source type")?;
    let mime = match ext {
        "html" => "text/html",
        "pdf" => "application/pdf",
        "zip" => "application/zip",
        _ => bail!("Invalid format"),
    };
    Ok(
        json!({"id":sid(url),"title":fname,"publisher":"EPD Danmark","url":url,"retrieved_at":info["retrieved_at"],"sha256":info["sha256"],
        "local_path":format!("{RAW}/{}.{ext}",info["sha256"].as_str().unwrap()),"media_type":mime,"license":LICENSE,"license_status":"unknown"}),
    )
}
fn inspect(e: &Entry, originals: &mut Originals, layouts: &Layouts) -> Result<Product> {
    if e.pdfs.len() != 1 {
        return Ok(Product::excluded("no_single_primary_A2_PDF"));
    }
    let page = originals.fetch(&e.detail, "html")?;
    let fields = detail(&fs::read_to_string(page)?);
    if fields
        .iter()
        .find(|(k, _)| k.starts_with("Antal deklarerede datasæt"))
        .map(|(_, v)| v.as_str())
        != Some("1")
    {
        return Ok(Product::excluded("dataset_count_absent_or_multiple"));
    }
    let basis = fields
        .get("Deklareret/Funktionel enhed")
        .map(String::as_str)
        .unwrap_or("");
    let Some(_) = reference(basis) else {
        return Ok(Product::excluded("complex_or_missing_reference_unit"));
    };
    let url = &e.pdfs[0];
    let path = originals.fetch(url, "pdf")?;
    let h = originals.seen[url]["sha256"].as_str().unwrap();
    if let Some(known) = layouts.known.get(h).filter(|k| k["reference"] == basis) {
        if known["status"] != "imported" {
            return Ok(Product::excluded(
                known["status"].as_str().context("layout review status")?,
            ));
        }
        let recipe = layouts
            .recipes
            .get(h)
            .context("Missing reviewed extraction map")?;
        if recipe.detail == e.detail
            && recipe.material["name"] == e.name
            && recipe.material["source_id"] == sid(url)
            && recipe.original_reference == basis
        {
            let cells = pdf::read_locked(&path, recipe)?;
            let rows = recipe
                .tables
                .iter()
                .zip(cells)
                .map(|(r, v)| ResultRow {
                    page: r.page,
                    line: r.line,
                    header: r.header,
                    indicator: r.indicator.clone(),
                    unit: r.unit.clone(),
                    modules: r.modules.clone(),
                    cells: v,
                })
                .collect();
            return result(
                recipe.material.clone(),
                basis,
                &recipe.reference_locator,
                rows,
                "pdftotext -layout",
            );
        }
    }
    match std::panic::catch_unwind(|| fresh::extract(e, &path, basis)) {
        Ok(parsed) => parsed,
        Err(_) => Ok(Product::excluded("unsupported_PDF_text")),
    }
}

pub fn run(args: Args) -> Result<Value> {
    let root = &args.root;
    let public = root.join(PUBLIC);
    let pinned = public.join("sources.lock.json");
    let lockfile = args.lock.as_deref().unwrap_or(&pinned);
    if args.refresh {
        ensure!(!lockfile.exists(), "Specify a new --lock path for refresh")
    }
    let lock = if args.refresh {
        Value::Null
    } else {
        serde_json::from_slice(&fs::read(lockfile)?)?
    };
    let mut reader =
        GzDecoder::new(&include_bytes!("../data/supplements/epd-danmark/pdf-layouts.json.gz")[..]);
    let mut data = String::new();
    reader.read_to_string(&mut data)?;
    let layouts: Layouts = serde_json::from_str(&data)?;
    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .user_agent("ft-materials/0.2")
        .build()?;
    let mut originals = Originals {
        root: root.clone(),
        client,
        expected: if args.refresh {
            None
        } else {
            Some(serde_json::from_value(lock["originals"].clone())?)
        },
        seen: BTreeMap::new(),
    };
    let index = originals.fetch(INDEX, "html")?;
    let (entries, bulk) = parse_index(&fs::read_to_string(index)?)?;
    originals.fetch(GPI, "pdf")?;
    let mut bulk_count = 0;
    if let Some(u) = bulk {
        let path = originals.fetch(&u, "zip")?;
        let z = zip::ZipArchive::new(Cursor::new(fs::read(path)?))?;
        for name in z.file_names() {
            if name?.to_lowercase().ends_with(".lb5epd") {
                bulk_count += 1;
            }
        }
    }
    let dest = args
        .output
        .unwrap_or_else(|| root.join("data/staging/epd-danmark"));
    let parent = dest.parent().context("missing parent")?;
    fs::create_dir_all(parent)?;
    let tmp = tempfile::tempdir_in(parent)?;
    let stage = tmp.path().join("bundle");
    fs::create_dir(&stage)?;
    let mut mats = fs::File::create(stage.join("materials.jsonl"))?;
    let mut obs = std::io::BufWriter::new(fs::File::create(stage.join("observations.jsonl"))?);
    let mut coverage = fs::File::create(stage.join("coverage.jsonl"))?;
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    let (mut nm, mut no, mut nn) = (0usize, 0usize, 0usize);
    let mut failed = BTreeMap::new();
    for e in &entries {
        let r = if lock["failed"].get(&e.detail).is_some() {
            Product::excluded("unavailable_at_snapshot")
        } else {
            match inspect(e, &mut originals, &layouts) {
                Ok(p) => p,
                Err(err) if args.refresh && err.chain().any(|e| e.is::<reqwest::Error>()) => {
                    failed.insert(&e.detail, format!("{err:#}"));
                    Product::excluded("unavailable_at_snapshot")
                }
                Err(err) => return Err(err.context(format!("Declaration {}", e.detail))),
            }
        };
        *counts.entry(r.status.clone()).or_default() += 1;
        coverage.write_all(&json_bytes(
            &json!({"detail":e.detail,"observations":r.obs.len(),"status":r.status}),
        )?)?;
        if let Some(m) = r.material {
            nm += 1;
            mats.write_all(&json_bytes(&m)?)?;
        }
        for v in r.obs {
            no += 1;
            if !v["value"].is_null() {
                nn += 1;
            }
            write_observation(&mut obs, &v)?;
        }
    }
    obs.flush()?;
    ensure!(nn > 0, "No verified EPD values were extracted");
    if !args.refresh {
        let refs = originals.expected.as_ref().unwrap().clone();
        for (u, item) in refs {
            if !originals.seen.contains_key(&u) {
                originals.fetch(&u, item["extension"].as_str().context("missing format")?)?;
            }
        }
    }
    let mut src = fs::File::create(stage.join("sources.jsonl"))?;
    for (u, item) in &originals.seen {
        src.write_all(&json_bytes(&source(u, item)?)?)?;
    }
    let mut slock = None;
    if args.refresh {
        slock = Some(json_bytes(
            &json!({"format":1,"collector_version":"rust-1","index":INDEX,"bulk_archive_members":bulk_count,"originals":originals.seen,"failed":failed}),
        )?);
    }
    let lock_hash = if let Some(s) = &slock {
        sha(s)
    } else {
        sha(&fs::read(lockfile)?)
    };
    let summary = json!({"dataset":"epd-danmark","sources":originals.seen.len(),"materials":nm,"observations":no,"numeric":nn,"explicit_source_markers":no-nn,
        "index_entries":entries.len(),"outcomes":counts,"source_lock_sha256":lock_hash,"bulk_lb5epd_members":bulk_count,"pdf_extractor":"native Rust pdf-extract 0.12.1","parser_version":"rust-1",
        "coverage":"EN 15804+A2; one confirmed reference and independently verified source cells","distribution":"Local download from EPD Danmark; EPD owners retain ownership."});
    let summaryfile = stage.join("summary.json");
    fs::write(&summaryfile, json_bytes(&summary)?)?;
    const RELEASE_LOCK: &str = "21c312d572114077ad5de568f7350058cb77d82f531fc5bb6d690bc026b9a0b7";
    if !args.refresh && lockfile == pinned {
        ensure!(
            lock_hash == RELEASE_LOCK,
            "Published source lock has changed"
        );
    }
    if !args.refresh && lock_hash == RELEASE_LOCK {
        let proof: Value = serde_json::from_slice(include_bytes!(
            "../data/supplements/epd-danmark/validation.json"
        ))?;
        for (file, h) in proof["bundled_file_sha256"]
            .as_object()
            .context("invalid validation manifest")?
        {
            ensure!(
                sha(&fs::read(stage.join(file))?) == h.as_str().unwrap(),
                "Pinned normalized {file} differs from independently checked dataset"
            );
        }
    }
    let already_present = dest.exists();
    if already_present {
        for name in [
            "sources.jsonl",
            "materials.jsonl",
            "observations.jsonl",
            "coverage.jsonl",
        ] {
            ensure!(
                fs::read(dest.join(name))? == fs::read(stage.join(name))?,
                "Existing bundle differs, select a new --output"
            );
        }
        let prev: Value = serde_json::from_slice(&fs::read(dest.join("summary.json"))?)?;
        ensure!(
            prev["source_lock_sha256"] == lock_hash,
            "Existing bundle belongs to another source edition"
        );
    }
    if let Some(b) = slock {
        ensure!(
            !lockfile.starts_with(&dest),
            "Source lock must be separate from the output bundle"
        );
        write_new(lockfile, &b)?;
    }
    if !already_present {
        fs::rename(&stage, &dest)?;
    }
    Ok(summary)
}

// Preserve the published decimal representation of very small finite values.
fn write_observation(mut writer: impl Write, v: &Value) -> Result<()> {
    let mut source = serde_json::to_string(v)?;
    if let Some(f) = v["value"].as_f64() {
        let normal = v["value"].to_string();
        let mut target = normal.clone();
        if let Some((coefficient, exp)) = normal.split_once('e') {
            let power: i32 = exp.parse()?;
            target = format!("{coefficient}e{power:+03}");
        } else if f != 0. && f.abs() < 1e-4 {
            let sci = format!("{f:e}");
            let (mantissa, exp) = sci.split_once('e').unwrap();
            let power: i32 = exp.parse()?;
            target = format!("{mantissa}e{power:+03}");
        }
        if normal != target {
            source = source.replace(
                &format!("\"value\":{normal},"),
                &format!("\"value\":{target},"),
            );
        }
    }
    writer.write_all(source.as_bytes())?;
    writer.write_all(b"\n")?;
    Ok(())
}
/// Text baselines reconstructed from the original PDF for source-locked maintenance records.
pub(crate) fn document_page_lines(doc: &pdf_extract::Document, page: u32) -> Result<Vec<String>> {
    Ok(pdf::extract_page(doc, page)?.lines())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ambiguous_thousands_and_unknown_units_have_no_reference() {
        assert_eq!(reference("1000 kg"), Some((1000.0, "kg".into())));
        assert_eq!(reference("1 m²"), Some((1.0, "m2".into())));
        for text in ["1.000 kg", "0 m²", "1 kg and 1 m²", "2.7 boxes"] {
            assert_eq!(reference(text), None);
        }
    }
    #[test]
    fn local_source_archives_are_immutable_and_validated() {
        let tmp = tempfile::tempdir().unwrap();
        let item =
            json!({"sha256":sha(b"accepted"),"extension":"html","bytes":8,"retrieved_at":"2020"});
        let mut originals = Originals {
            root: tmp.path().into(),
            client: Client::new(),
            expected: Some(BTreeMap::from([(INDEX.into(), item.clone())])),
            seen: BTreeMap::new(),
        };
        let path = originals.local(&item).unwrap();
        write_new(&path, b"accepted").unwrap();
        assert!(write_new(&path, b"different").is_err());
        assert_eq!(originals.fetch(INDEX, "html").unwrap(), path);
        originals.seen.clear();
        fs::write(&path, b"corrupt").unwrap();
        assert!(originals.fetch(INDEX, "html").is_err());
    }
}
