use anyhow::{Context, Result, bail, ensure};
use flate2::read::MultiGzDecoder;
use parquet::file::reader::{FileReader, SerializedFileReader};
use parquet::record::Field;
use rusqlite::{Connection, params, params_from_iter, types::Value as Sql};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, HashMap},
    fs::{self, File},
    io::{BufRead, BufReader, Read, Write},
    path::{Component, Path, PathBuf},
};
use unicode_normalization::{UnicodeNormalization, char::is_combining_mark};

const RAW: [&str; 5] = [
    "datasets",
    "sources",
    "materials",
    "observations",
    "build_info",
];
const STREAMS: [&str; 3] = ["sources", "materials", "observations"];
const SCHEMA: &str = include_str!("../data/unified/schema.sql");
const VOCAB: &str = include_str!("../data/unified/vocabulary.json");
pub fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str> {
    v.get(key)
        .and_then(Value::as_str)
        .filter(|s| !s.trim().is_empty())
        .with_context(|| format!("Missing string {key}"))
}
pub fn read(path: &Path) -> Result<Value> {
    serde_json::from_reader(BufReader::new(
        File::open(path).with_context(|| path.display().to_string())?,
    ))
    .with_context(|| path.display().to_string())
}
pub fn hash(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
pub fn file_hash(path: &Path) -> Result<String> {
    let mut h = Sha256::new();
    let mut reader = BufReader::with_capacity(1024 * 1024, File::open(path)?);
    std::io::copy(&mut reader, &mut h)?;
    Ok(hex::encode(h.finalize()))
}
fn json_write(path: &Path, v: &Value) -> Result<()> {
    let mut f = tempfile::NamedTempFile::new_in(path.parent().context("Missing parent")?)?;
    serde_json::to_writer_pretty(&mut f, v)?;
    writeln!(f)?;
    f.as_file().sync_all()?;
    f.persist(path)?;
    Ok(())
}
fn safe_relative(path: &str) -> Result<&Path> {
    let p = Path::new(path);
    ensure!(
        !path.is_empty() && p.components().all(|c| matches!(c, Component::Normal(_))),
        "Invalid relative path {path}"
    );
    Ok(p)
}
fn checked_path(root: &Path, name: &str) -> Result<PathBuf> {
    let path = root.join(safe_relative(name)?);
    if path.exists() {
        ensure!(
            path.canonicalize()?.starts_with(root.canonicalize()?),
            "Source path leaves root"
        );
    }
    Ok(path)
}
pub fn fold(s: &str) -> String {
    s.to_lowercase()
        .replace('æ', "ae")
        .replace('ø', "o")
        .nfkd()
        .filter(|c| !is_combining_mark(*c))
        .collect()
}
fn bundle(folder: &Path) -> Result<BTreeMap<String, String>> {
    let mut out = BTreeMap::from([(
        "summary.json".to_owned(),
        file_hash(&folder.join("summary.json"))?,
    )]);
    for table in STREAMS {
        let opts = [format!("{table}.jsonl"), format!("{table}.jsonl.gz")];
        let found: Vec<_> = opts.iter().filter(|p| folder.join(p).is_file()).collect();
        ensure!(
            found.len() == 1,
            "Expected one {table} stream in {}",
            folder.display()
        );
        out.insert(found[0].clone(), file_hash(&folder.join(found[0]))?);
    }
    Ok(out)
}
fn add_schemas(db: &Connection, manifest: &Value, kind: &str) -> Result<()> {
    for obj in manifest["sqlite_schema"]
        .as_array()
        .context("Invalid Parquet schema")?
    {
        if obj["type"] == kind {
            db.execute_batch(text(obj, "sql")?)?;
        }
    }
    Ok(())
}
fn counts(db: &Connection) -> Result<Value> {
    let mut out = json!({});
    for table in ["datasets", "materials", "sources", "observations"] {
        out[table] = db
            .query_row(&format!("SELECT count(*) FROM {table}"), [], |r| {
                r.get::<_, i64>(0)
            })?
            .into();
    }
    Ok(out)
}
fn coverage(db: &Connection) -> Result<Value> {
    let mut out = json!({});
    for table in STREAMS {
        let mut st = db.prepare(&format!(
            "SELECT dataset_id,count(*) FROM {table} GROUP BY dataset_id"
        ))?;
        for row in st.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?)))? {
            let (ds, count) = row?;
            out[ds][table] = count.into();
        }
    }
    Ok(out)
}
fn audit(db: &Connection) -> Result<()> {
    ensure!(
        db.prepare("PRAGMA foreign_key_check")?
            .query([])?
            .next()?
            .is_none(),
        "Foreign-key check failed"
    );
    ensure!(
        db.query_row("PRAGMA quick_check", [], |r| r.get::<_, String>(0))? == "ok",
        "SQLite quick_check failed"
    );
    Ok(())
}
fn classify(db: &Connection) -> Result<()> {
    let vocabulary: Value = serde_json::from_str(VOCAB)?;
    let mut map = HashMap::new();
    for (canonical, names) in vocabulary["properties"]
        .as_object()
        .context("Invalid vocabulary")?
    {
        for raw in names.as_array().context("Invalid property names")? {
            let name = raw.as_str().context("Invalid alias")?;
            ensure!(
                map.insert(name, format!("property:{canonical}")).is_none(),
                "Duplicate property alias {name}"
            );
        }
    }
    db.execute_batch(SCHEMA)?;
    let mut src = db.prepare("SELECT DISTINCT dataset_id,property FROM observations")?;
    let mut ins = db.prepare("INSERT INTO property_map VALUES (?,?,?)")?;
    for row in src.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))? {
        let (ds, raw) = row?;
        let prop = map
            .get(raw.as_str())
            .cloned()
            .unwrap_or_else(|| format!("source-property:{ds}:{raw}"));
        ins.execute(params![ds, raw, prop])?;
    }
    db.execute_batch("INSERT INTO material_citations SELECT DISTINCT m.id,m.source_id,m.source_locator,s.id FROM materials m JOIN observations o ON o.material_id=m.id JOIN sources s ON s.url=json_extract(o.conditions_json,'$.underlying_source_url') AND s.dataset_id='br18' WHERE m.dataset_id='br18'")?;
    Ok(())
}
fn freeze(path: &Path) -> Result<()> {
    let mut p = path.metadata()?.permissions();
    p.set_readonly(true);
    fs::set_permissions(path, p)?;
    Ok(())
}
const BUILD_MARKER: &str = ".ft-materials-build";
const OWNER: &[u8] = b"ft-materials database builder v2";

fn workdir(store: &Path, prefix: &str) -> Result<tempfile::TempDir> {
    let temp = tempfile::Builder::new().prefix(prefix).tempdir_in(store)?;
    fs::write(temp.path().join(BUILD_MARKER), OWNER)?;
    Ok(temp)
}

// Called only while holding the exclusive store build lock. Interrupted imports
// can leave gigabytes of SQLite pages. A private marker and expected filenames
// distinguish our incomplete builds from user directories and pinned editions.
fn clear_interrupted(store: &Path) -> Result<()> {
    for entry in fs::read_dir(store)? {
        let entry = entry?;
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if !(name.starts_with(".base-") || name.starts_with(".edition-"))
            || !entry.file_type()?.is_dir()
        {
            continue;
        }
        let path = entry.path();
        if fs::read(path.join(BUILD_MARKER)).ok().as_deref() != Some(OWNER) {
            continue;
        }
        let expected_files = fs::read_dir(&path)?.all(|child| {
            child.is_ok_and(|f| {
                f.file_type().is_ok_and(|t| t.is_file())
                    && matches!(
                        f.file_name().to_str(),
                        Some(
                            ".ft-materials-build"
                                | "materials.sqlite"
                                | "supplement.sqlite"
                                | "materials.sqlite-journal"
                                | "supplement.sqlite-journal"
                                | "manifest.json"
                        )
                    )
            })
        });
        if expected_files {
            fs::remove_dir_all(path)?;
        }
    }
    Ok(())
}

fn publish_dir(temp: tempfile::TempDir, dest: &Path) -> Result<()> {
    match fs::rename(temp.path(), dest) {
        Ok(()) => Ok(()),
        Err(_) if dest.join("manifest.json").is_file() => Ok(()),
        Err(e) => Err(e.into()),
    }
}
fn parquet_restore(db: &mut Connection, dir: &Path, manifest: &Value) -> Result<()> {
    ensure!(
        manifest["format_version"] == 1,
        "Unsupported Parquet format"
    );
    db.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")?;
    let tx = db.transaction()?;
    add_schemas(&tx, manifest, "table")?;
    for table in RAW {
        let cols = manifest["tables"][table]["columns"]
            .as_array()
            .context("Missing columns")?;
        let names: Vec<_> = cols
            .iter()
            .map(|c| text(c, "name"))
            .collect::<Result<_>>()?;
        let mut insert = tx.prepare(&format!(
            "INSERT INTO {table} VALUES ({})",
            vec!["?"; names.len()].join(",")
        ))?;
        let mut total = 0u64;
        for item in manifest["files"]
            .as_array()
            .context("Missing Parquet files")?
        {
            let name = text(item, "path")?;
            if name != format!("{table}.parquet") && !name.starts_with(&format!("{table}/")) {
                continue;
            }
            let path = checked_path(dir, name)?;
            ensure!(
                file_hash(&path)? == text(item, "sha256")?,
                "Parquet checksum differs: {name}"
            );
            let file = SerializedFileReader::new(File::open(&path)?)?;
            let actual: Vec<_> = file
                .metadata()
                .file_metadata()
                .schema_descr()
                .columns()
                .iter()
                .map(|c| c.name())
                .collect();
            ensure!(actual == names, "Unexpected Parquet columns: {name}");
            let mut seen = 0;
            for row in file.get_row_iter(None)? {
                let values = row?
                    .into_columns()
                    .into_iter()
                    .map(|(_, c)| match c {
                        Field::Null => Ok(Sql::Null),
                        Field::Str(s) => Ok(Sql::Text(s)),
                        Field::Double(v) if v.is_finite() => Ok(Sql::Real(v)),
                        Field::Long(v) => Ok(Sql::Integer(v)),
                        Field::Int(v) => Ok(Sql::Integer(v.into())),
                        other => bail!("Unexpected Parquet field {other:?}"),
                    })
                    .collect::<Result<Vec<_>>>()?;
                insert.execute(params_from_iter(values))?;
                seen += 1;
            }
            ensure!(
                item["rows"].as_u64() == Some(seen),
                "Wrong row count in {name}"
            );
            total += seen;
        }
        ensure!(
            manifest["tables"][table]["rows"].as_u64() == Some(total),
            "Incomplete table {table}"
        );
        eprintln!("Restored {table}: {total}");
    }
    add_schemas(&tx, manifest, "index")?;
    tx.commit()?;
    Ok(())
}
fn checked_manifest(path: &Path, inputs: &Value, prefix: &str) -> Result<Value> {
    let m = read(&path.join("manifest.json"))?;
    ensure!(
        &m["inputs"] == inputs && m["snapshot"] == identity(prefix, inputs)?,
        "Invalid installed manifest"
    );
    Ok(m)
}
fn identity(prefix: &str, inputs: &Value) -> Result<String> {
    Ok(format!("{prefix}-{}", hash(&serde_json::to_vec(inputs)?)))
}
fn ensure_base(root: &Path, store: &Path, base: &Value) -> Result<(PathBuf, Value)> {
    let base_id = identity("base2", base)?;
    let dest = store.join(&base_id);
    if !dest.is_dir() {
        let temp = workdir(store, ".base-")?;
        let dbfile = temp.path().join("materials.sqlite");
        let parquet = root.join("data/parquet");
        let metadata = read(&parquet.join("manifest.json"))?;
        // The source-controlled manifest pins the schema and individual Parquet files.
        let mut db = Connection::open(&dbfile)?;
        parquet_restore(&mut db, &parquet, &metadata)?;
        let tx = db.transaction()?;
        classify(&tx)?;
        tx.execute(
            "INSERT INTO build_info VALUES ('unified_base',?)",
            [&base_id],
        )?;
        tx.commit()?;
        audit(&db)?;
        let m = json!({"snapshot":base_id,"inputs":base,"counts":counts(&db)?,"datasets":coverage(&db)?,"database_sha256":file_hash(&dbfile)?});
        drop(db);
        freeze(&dbfile)?;
        json_write(&temp.path().join("manifest.json"), &m)?;
        publish_dir(temp, &dest)?;
    }
    let m = checked_manifest(&dest, base, "base2")?;
    Ok((dest, m))
}
fn records(folder: &Path, table: &str, mut consume: impl FnMut(Value) -> Result<()>) -> Result<()> {
    let mut name = folder.join(format!("{table}.jsonl"));
    let input: Box<dyn Read> = if name.is_file() {
        Box::new(File::open(&name)?)
    } else {
        name = folder.join(format!("{table}.jsonl.gz"));
        Box::new(MultiGzDecoder::new(File::open(&name)?))
    };
    for (i, line) in BufReader::new(input).lines().enumerate() {
        let line = line?;
        if !line.trim().is_empty() {
            let v = serde_json::from_str(&line)
                .with_context(|| format!("{}:{}", name.display(), i + 1))?;
            consume(v).with_context(|| format!("{}:{}", name.display(), i + 1))?;
        }
    }
    Ok(())
}
fn source_check(
    o: &Value,
    root: &Path,
    required: bool,
    seen: &mut HashMap<PathBuf, String>,
) -> Result<()> {
    let expected = text(o, "sha256")?;
    ensure!(is_sha(expected), "Invalid source hash");
    let path = checked_path(root, text(o, "local_path")?)?;
    if path.is_file() {
        if !seen.contains_key(&path) {
            seen.insert(path.clone(), file_hash(&path)?);
        }
        ensure!(
            seen[&path] == expected,
            "Original checksum failed: {}",
            path.display()
        );
    } else {
        ensure!(!required, "Missing original {}", path.display());
    }
    Ok(())
}
fn opt<'a>(v: &'a Value, k: &str) -> Option<&'a str> {
    v.get(k).and_then(Value::as_str)
}
fn load_bundle(db: &Connection, folder: &Path, root: &Path, required: bool) -> Result<()> {
    let ds = folder
        .file_name()
        .and_then(|s| s.to_str())
        .context("Invalid supplement path")?;
    let summary = read(&folder.join("summary.json"))?;
    ensure!(
        summary["dataset"] == ds,
        "Dataset name and directory differ"
    );
    db.execute(
        "INSERT INTO datasets VALUES (?,?)",
        params![ds, summary.to_string()],
    )?;
    let mut seen = HashMap::new();
    records(folder, "sources", |o| {
        source_check(&o, root, required, &mut seen)?;
        db.execute(
            "INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            params![
                text(&o, "id")?,
                ds,
                text(&o, "title")?,
                opt(&o, "publisher"),
                text(&o, "url")?,
                text(&o, "retrieved_at")?,
                text(&o, "local_path")?,
                text(&o, "sha256")?,
                opt(&o, "media_type"),
                text(&o, "license")?,
                text(&o, "license_status")?,
                o.to_string()
            ],
        )?;
        Ok(())
    })?;
    records(folder, "materials", |m| {
        let aliases = m.get("aliases").cloned().unwrap_or(json!([]));
        let mut words = vec![text(&m, "name")?, text(&m, "category")?];
        for a in aliases.as_array().context("Invalid aliases")? {
            words.push(a.as_str().context("Expected text alias")?);
        }
        db.execute(
            "INSERT INTO materials VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            params![
                text(&m, "id")?,
                ds,
                text(&m, "name")?,
                text(&m, "kind")?,
                text(&m, "category")?,
                aliases.to_string(),
                opt(&m, "description"),
                text(&m, "source_id")?,
                text(&m, "source_locator")?,
                fold(&words.join(" ")),
                m.to_string()
            ],
        )?;
        Ok(())
    })?;
    records(folder, "observations", |o| {
        let value = observation_value(&o)?;
        let cond = o.get("conditions").cloned().unwrap_or(json!({}));
        ensure!(cond.is_object(), "Invalid observation conditions");
        db.execute(
            "INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            params![
                text(&o, "id")?,
                ds,
                text(&o, "material_id")?,
                text(&o, "property")?,
                value,
                text(&o, "value_text")?,
                opt(&o, "unit"),
                opt(&o, "module"),
                opt(&o, "declared_unit"),
                opt(&o, "basis"),
                opt(&o, "method"),
                opt(&o, "data_status").unwrap_or("reported"),
                cond.to_string(),
                text(&o, "source_id")?,
                text(&o, "source_locator")?,
                o.to_string()
            ],
        )?;
        Ok(())
    })?;
    for table in STREAMS {
        if let Some(expected) = summary[table].as_u64() {
            let n: i64 = db.query_row(
                &format!("SELECT count(*) FROM {table} WHERE dataset_id=?"),
                [ds],
                |r| r.get(0),
            )?;
            ensure!(
                Some(expected) == u64::try_from(n).ok(),
                "Incorrect {table} count in {ds}"
            );
        }
    }
    Ok(())
}
fn observation_value(o: &Value) -> Result<Option<f64>> {
    let value = if o["value"].is_null() {
        None
    } else {
        Some(
            o["value"]
                .as_f64()
                .filter(|v| v.is_finite())
                .context("Invalid scalar")?,
        )
    };
    let kind = opt(o, "value_kind").unwrap_or(if value.is_some() { "scalar" } else { "text" });
    match kind {
        "scalar" => ensure!(value.is_some(), "Missing scalar"),
        "curve" => {
            let c = &o["structured_value"];
            let x = c["x_values"].as_array().context("Missing x_values")?;
            let y = c["y_values"].as_array().context("Missing y_values")?;
            ensure!(
                !x.is_empty()
                    && x.len() == y.len()
                    && x.iter()
                        .chain(y)
                        .all(|v| v.as_f64().is_some_and(f64::is_finite)),
                "Invalid curve"
            );
            text(c, "x_unit")?;
            text(c, "x_property")?;
            text(o, "unit")?;
        }
        "range" => {
            let r = &o["structured_value"];
            ensure!(
                r["min"]
                    .as_f64()
                    .zip(r["max"].as_f64())
                    .is_some_and(|(a, b)| a <= b),
                "Invalid range"
            );
        }
        "missing" | "text" | "classification" => {}
        _ => bail!("Unknown observation kind {kind}"),
    }
    ensure!(
        kind == "scalar" || value.is_none(),
        "Non-scalar contains a single numeric value"
    );
    Ok(value)
}
fn is_sha(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn attach(db: &Connection, path: &Path, name: &str) -> Result<()> {
    let uri = reqwest::Url::from_file_path(path.canonicalize()?)
        .map_err(|_| anyhow::anyhow!("Invalid database path"))?;
    db.execute(
        &format!("ATTACH ? AS {name}"),
        [format!("{uri}?mode=ro&immutable=1")],
    )?;
    Ok(())
}
pub struct Edition {
    pub id: String,
    pub manifest: Value,
    pub db: Connection,
    pub base: PathBuf,
    pub overlay: PathBuf,
}
pub fn open(store: &Path, spec: &str) -> Result<Edition> {
    let id = if spec == "latest" {
        text(
            &read(&store.join("latest.json"))
                .context("No active edition. Run ft-materials build")?,
            "snapshot",
        )?
        .to_string()
    } else {
        spec.to_owned()
    };
    ensure!(
        id.strip_prefix("u2-").is_some_and(is_sha),
        "Invalid edition ID"
    );
    let dir = store.join(&id);
    let m = read(&dir.join("manifest.json"))?;
    ensure!(
        text(&m, "snapshot")? == id && identity("u2", &m["inputs"])? == id,
        "Edition identity mismatch"
    );
    let bid = identity("base2", &m["inputs"]["base"])?;
    let bdir = store.join(&bid);
    let base = bdir.join("materials.sqlite");
    let overlay = dir.join("supplement.sqlite");
    let bm = checked_manifest(&bdir, &m["inputs"]["base"], "base2")?;
    ensure!(
        bm["database_sha256"] == m["base_sha256"],
        "Base manifest mismatch"
    );
    let db = Connection::open_in_memory()?;
    attach(&db, &base, "foundation")?;
    attach(&db, &overlay, "extra")?;
    let marker: String = db.query_row(
        "SELECT value FROM extra.build_info WHERE key='unified_snapshot'",
        [],
        |r| r.get(0),
    )?;
    ensure!(marker == id, "Edition database mismatch");
    let marker: String = db.query_row(
        "SELECT value FROM foundation.build_info WHERE key='unified_base'",
        [],
        |r| r.get(0),
    )?;
    ensure!(marker == bid, "Base database mismatch");
    for table in [
        "datasets",
        "sources",
        "materials",
        "observations",
        "build_info",
        "property_map",
        "material_links",
        "material_citations",
        "unified_materials",
        "unified_sources",
        "unified_observations",
    ] {
        db.execute_batch(&format!("CREATE TEMP VIEW {table} AS SELECT * FROM foundation.{table} UNION ALL SELECT * FROM extra.{table}"))?;
    }
    db.execute_batch("PRAGMA query_only=ON")?;
    Ok(Edition {
        id,
        manifest: m,
        db,
        base,
        overlay,
    })
}
fn inputs(root: &Path, folders: &[PathBuf]) -> Result<Value> {
    let mut supplements = BTreeMap::new();
    for f in folders {
        let name = f
            .file_name()
            .and_then(|s| s.to_str())
            .context("Invalid supplement name")?;
        ensure!(
            !name.is_empty()
                && name.bytes().all(|b| b.is_ascii_lowercase()
                    || b.is_ascii_digit()
                    || b == b'-'
                    || b == b'_'),
            "Invalid dataset name {name}"
        );
        ensure!(
            supplements.insert(name, bundle(f)?).is_none(),
            "Duplicate dataset {name}"
        );
    }
    Ok(
        json!({"base":{"format":2,"parquet_manifest_sha256":file_hash(&root.join("data/parquet/manifest.json"))?,"schema_sha256":hash(SCHEMA.as_bytes()),"vocabulary_sha256":hash(VOCAB.as_bytes())},"supplements":supplements}),
    )
}
pub fn build(
    root: &Path,
    store: &Path,
    folders: &[PathBuf],
    expected: Option<&str>,
    activate: bool,
    required: bool,
) -> Result<Value> {
    let input = inputs(root, folders)?;
    let id = identity("u2", &input)?;
    ensure!(
        expected.is_none_or(|v| v == id),
        "Input hash mismatch. Computed {id}"
    );
    fs::create_dir_all(store)?;
    let lock = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(store.join(".build.lock"))?;
    lock.lock()?;
    clear_interrupted(store)?;
    let (base, bm) = ensure_base(root, store, &input["base"])?;
    let dir = store.join(&id);
    if !dir.is_dir() {
        let tmp = workdir(store, ".edition-")?;
        let overlay = tmp.path().join("supplement.sqlite");
        let mut db = Connection::open(&overlay)?;
        db.execute_batch("PRAGMA foreign_keys=ON")?;
        attach(&db, &base.join("materials.sqlite"), "foundation")?;
        let meta = read(&root.join("data/parquet/manifest.json"))?;
        let tx = db.transaction()?;
        add_schemas(&tx, &meta, "table")?;
        for folder in folders {
            load_bundle(&tx, folder, root, required)?;
        }
        add_schemas(&tx, &meta, "index")?;
        classify(&tx)?;
        for table in ["datasets", "sources", "materials", "observations"] {
            let q = format!(
                "SELECT e.id FROM main.{table} e JOIN foundation.{table} b ON b.id=e.id LIMIT 1"
            );
            ensure!(
                tx.prepare(&q)?.query([])?.next()?.is_none(),
                "ID collision between base and supplement in {table}"
            );
        }
        for folder in folders {
            records(folder, "materials", |m| {
                if let Some(links) = m["links"].as_array() {
                    for link in links {
                        tx.execute(
                            "INSERT INTO material_links VALUES (?,?,?,?,?)",
                            params![
                                text(&m, "id")?,
                                text(link, "relation")?,
                                text(link, "target_id")?,
                                text(link, "source_id")?,
                                text(link, "source_locator")?
                            ],
                        )?;
                    }
                }
                Ok(())
            })?;
        }
        tx.execute(
            "INSERT INTO build_info VALUES ('unified_snapshot',?)",
            [&id],
        )?;
        tx.commit()?;
        audit(&db)?;
        let mut totals = bm["counts"].clone();
        for (table, n) in counts(&db)?.as_object().context("Invalid counts")? {
            totals[table] = json!(totals[table].as_u64().unwrap_or(0) + n.as_u64().unwrap_or(0));
        }
        let mut ds = bm["datasets"].clone();
        for (k, v) in coverage(&db)?.as_object().context("Invalid coverage")? {
            ds[k] = v.clone();
        }
        drop(db);
        freeze(&overlay)?;
        ensure!(
            inputs(root, folders)? == input,
            "Source inputs changed during build"
        );
        let manifest = json!({"snapshot":id,"inputs":input,"counts":totals,"datasets":ds,"base_sha256":bm["database_sha256"],"supplement_sha256":file_hash(&overlay)?});
        json_write(&tmp.path().join("manifest.json"), &manifest)?;
        publish_dir(tmp, &dir)?;
    } else if required {
        let mut seen = HashMap::new();
        for f in folders {
            records(f, "sources", |o| source_check(&o, root, true, &mut seen))?;
        }
    }
    let edition = open(store, &id)?;
    if activate {
        json_write(&store.join("latest.json"), &json!({"snapshot":id}))?;
    }
    Ok(edition.manifest)
}
pub fn verify(e: &Edition) -> Result<Value> {
    let b = file_hash(&e.base)?;
    let s = file_hash(&e.overlay)?;
    let ok = e.manifest["base_sha256"] == b && e.manifest["supplement_sha256"] == s;
    Ok(json!({"ok":ok,"snapshot":e.id,"base_sha256":b,"supplement_sha256":s}))
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_curve_and_typed_values() {
        assert!(observation_value(&json!({"value":null,"value_kind":"curve","structured_value":{"x_values":[1,2],"y_values":[0]}})).is_err());
        assert!(
            observation_value(
                &json!({"value":null,"value_kind":"range","structured_value":{"min":1,"max":2}})
            )
            .is_ok()
        );
        assert_eq!(
            observation_value(&json!({"value":0,"value_kind":"scalar"})).unwrap(),
            Some(0.0)
        );
    }
    #[test]
    fn abandoned_build_cleanup_only_removes_our_known_work_files() -> Result<()> {
        let root = tempfile::tempdir()?;
        let ours = workdir(root.path(), ".base-")?.keep();
        fs::write(ours.join("materials.sqlite"), b"partial")?;
        let foreign = workdir(root.path(), ".edition-")?.keep();
        fs::write(foreign.join("notes.txt"), b"user notes")?;
        let edition = root.path().join("u2-pinned");
        fs::create_dir(&edition)?;
        clear_interrupted(root.path())?;
        assert!(!ours.exists());
        assert!(foreign.join("notes.txt").exists() && edition.exists());
        Ok(())
    }
    #[test]
    fn paths_and_ids() {
        assert!(safe_relative("../materials").is_err());
        assert!(!is_sha("../a"));
        assert_eq!(fold("Bøgetræ"), "bogetrae");
    }
}
