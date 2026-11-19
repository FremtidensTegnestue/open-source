//! Check exactly the source IDs selected from a snapshot against current publisher bytes.
use anyhow::{Context, Result, ensure};
use clap::Args as ClapArgs;
use reqwest::{Url, blocking::Client};
use rusqlite::{Connection, OptionalExtension, Row};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    io::Read,
    time::Duration,
};

#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Registered source ID. Repeat to select multiple sources.
    #[arg(
        long = "source",
        visible_alias = "source-id",
        required_unless_present = "dataset",
        conflicts_with = "dataset"
    )]
    pub sources: Vec<String>,
    /// Check the sources of this dataset, ordered by source ID.
    #[arg(long, required_unless_present = "sources")]
    pub dataset: Option<String>,
    /// Limit a dataset check to the first N source IDs.
    #[arg(long,requires="dataset",conflicts_with="sources",value_parser=clap::value_parser!(u32).range(1..))]
    pub limit: Option<u32>,
    /// Publisher request timeout in seconds.
    #[arg(long,default_value_t=20,value_parser=clap::value_parser!(u64).range(1..=60))]
    pub timeout: u64,
}

struct Source {
    id: String,
    dataset: String,
    url: String,
    sha: String,
}
impl Source {
    fn read(row: &Row<'_>) -> rusqlite::Result<Self> {
        Ok(Self {
            id: row.get(0)?,
            dataset: row.get(1)?,
            url: row.get(2)?,
            sha: row.get(3)?,
        })
    }
}

fn select(db: &Connection, args: &Args) -> Result<(Vec<Source>, Value)> {
    if let Some(dataset) = &args.dataset {
        ensure!(
            args.sources.is_empty() && args.limit != Some(0),
            "Select one dataset or explicit sources"
        );
        ensure!(
            db.query_row(
                "SELECT EXISTS(SELECT 1 FROM datasets WHERE id=?1)",
                [dataset],
                |r| r.get::<_, bool>(0)
            )?,
            "Unknown dataset: {dataset}"
        );
        let count: i64 = db.query_row(
            "SELECT count(*) FROM sources WHERE dataset_id=?1",
            [dataset],
            |r| r.get(0),
        )?;
        let mut stmt = db.prepare(
            "SELECT id,dataset_id,url,sha256 FROM sources WHERE dataset_id=?1 ORDER BY id LIMIT ?2",
        )?;
        let rows = stmt
            .query_map(
                rusqlite::params![dataset, args.limit.map(i64::from).unwrap_or(-1)],
                Source::read,
            )?
            .collect::<rusqlite::Result<Vec<_>>>()?;
        let scope = json!({"dataset":dataset,"available_sources":count,"limit":args.limit,"selection_order":"source_id","all_dataset_sources_selected":rows.len() as i64==count});
        Ok((rows, scope))
    } else {
        ensure!(
            !args.sources.is_empty() && args.limit.is_none(),
            "Select explicit sources or a dataset"
        );
        let ids: BTreeSet<&String> = args.sources.iter().collect();
        let mut stmt = db.prepare("SELECT id,dataset_id,url,sha256 FROM sources WHERE id=?1")?;
        let rows = ids
            .iter()
            .map(|id| {
                stmt.query_row([id], Source::read)
                    .optional()?
                    .with_context(|| format!("Unknown source: {id}"))
            })
            .collect::<Result<_>>()?;
        Ok((rows, json!({"explicit_sources":ids})))
    }
}

fn fetch(client: &Client, url: &str) -> Value {
    let Ok(parsed) = Url::parse(url) else {
        return json!({"failure":"invalid_url"});
    };
    if !matches!(parsed.scheme(), "http" | "https") {
        return json!({"failure":"unsupported_url_scheme"});
    }
    let mut response = match client
        .get(parsed)
        .header("Accept-Encoding", "identity")
        .send()
    {
        Ok(r) => r,
        Err(e) => return json!({"failure":if e.is_timeout(){"timeout"}else{"network_error"}}),
    };
    if response.status().as_u16() != 200 {
        return json!({"failure":"http_status","http_status":response.status().as_u16()});
    }
    let length = response.content_length();
    let mut count = 0u64;
    let mut digest = Sha256::new();
    let mut block = [0u8; 64 * 1024];
    loop {
        match response.read(&mut block) {
            Ok(0) => break,
            Ok(n) => {
                count += n as u64;
                digest.update(&block[..n]);
            }
            Err(e) => {
                return json!({"failure":if e.kind()==std::io::ErrorKind::TimedOut{"timeout"}else{"response_error"},"received_bytes":count});
            }
        }
    }
    if length.is_some_and(|len| len != count) {
        return json!({"failure":"incomplete_response","received_bytes":count});
    }
    json!({"current_sha256":hex::encode(digest.finalize()),"received_bytes":count})
}

pub fn run(args: Args, db: &Connection) -> Result<Value> {
    ensure!(
        (1..=60).contains(&args.timeout),
        "Timeout must be 1–60 seconds"
    );
    let (sources, scope) = select(db, &args)?;
    let urls: Vec<_> = sources
        .iter()
        .map(|s| s.url.as_str())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let client = Client::builder()
        .user_agent("FremtidensTegnestue-SourceCheck/1")
        .timeout(Duration::from_secs(args.timeout))
        .build()?;
    let responses = std::thread::scope(|scope| {
        let mut jobs = Vec::new();
        let chunk_size = urls.len().div_ceil(4).max(1);
        for group in urls.chunks(chunk_size) {
            let client = &client;
            jobs.push(scope.spawn(move || {
                group
                    .iter()
                    .map(|&u| (u, fetch(client, u)))
                    .collect::<Vec<_>>()
            }));
        }
        let mut responses = BTreeMap::new();
        for job in jobs {
            responses.extend(
                job.join()
                    .map_err(|_| anyhow::anyhow!("Publisher worker failed"))?,
            );
        }
        Ok::<_, anyhow::Error>(responses)
    })?;
    let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
    let mut results = Vec::new();
    for source in &sources {
        let response = &responses[source.url.as_str()];
        let status = if response.get("failure").is_some() {
            "check_failed"
        } else if response["current_sha256"] == source.sha {
            "identical_bytes"
        } else {
            "changed_bytes"
        };
        *counts.entry(status).or_default() += 1;
        let mut r = json!({"id":source.id,"dataset":source.dataset,"url":source.url,"snapshot_sha256":source.sha,"status":status});
        r.as_object_mut()
            .unwrap()
            .extend(response.as_object().unwrap().clone());
        results.push(r);
    }
    let snapshot: Option<String> = db
        .query_row(
            "SELECT value FROM build_info WHERE key='unified_snapshot'",
            [],
            |r| r.get(0),
        )
        .optional()?;
    Ok(
        json!({"snapshot":snapshot,"scope":scope,"checked_sources":sources.len(),"distinct_urls":urls.len(),"status_counts":counts,
        "comparison":"SHA-256 of full responses at the selected registered URLs. A publisher may publish newer editions at other URLs.",
        "results":results}),
    )
}
