#[path = "../src/updates.rs"]
mod updates;

use clap::Parser;
use rusqlite::{Connection, params};
use sha2::{Digest, Sha256};
use std::{
    io::{BufRead, BufReader, Write},
    net::TcpListener,
};

#[derive(Parser)]
struct Command {
    #[command(flatten)]
    args: updates::Args,
}

fn db() -> Connection {
    let db = Connection::open_in_memory().unwrap();
    db.execute_batch(
        "CREATE TABLE sources(id TEXT,dataset_id TEXT,url TEXT,sha256 TEXT);
        CREATE TABLE datasets(id TEXT);
        CREATE TABLE build_info(key TEXT,value TEXT);
        INSERT INTO datasets VALUES('test'),('empty');
        INSERT INTO build_info VALUES('unified_snapshot','u1-offline-test');",
    )
    .unwrap();
    db
}
fn args(argv: &[&str]) -> updates::Args {
    Command::try_parse_from(std::iter::once("check-updates").chain(argv.iter().copied()))
        .unwrap()
        .args
}

#[test]
fn response_bytes_order_selection_scope_dedup_and_http_errors() {
    let server = TcpListener::bind("127.0.0.1:0").unwrap();
    let base = format!("http://{}", server.local_addr().unwrap());
    let worker = std::thread::spawn(move || {
        let mut paths = Vec::new();
        for mut stream in server.incoming().take(2).map(|c| c.unwrap()) {
            let mut first = String::new();
            BufReader::new(&stream).read_line(&mut first).unwrap();
            let path = first.split_whitespace().nth(1).unwrap().to_owned();
            let status = if path == "/ab" {
                "200 OK"
            } else {
                "404 Not Found"
            };
            write!(
                stream,
                "HTTP/1.1 {status}\r\nContent-Length: 1\r\nConnection: close\r\n\r\nx"
            )
            .unwrap();
            paths.push(path);
        }
        paths.sort();
        paths
    });
    let db = db();
    let matches = hex::encode(Sha256::digest(b"x"));
    let changed = hex::encode(Sha256::digest(b"older"));
    for (id, path, sha) in [
        ("C", "/c", &changed),
        ("B", "/ab", &changed),
        ("A", "/ab", &matches),
        ("D", "/unselected", &changed),
    ] {
        db.execute(
            "INSERT INTO sources VALUES(?1,'test',?2,?3)",
            params![id, format!("{base}{path}"), sha],
        )
        .unwrap();
    }
    let output = updates::run(
        args(&["--dataset", "test", "--limit", "3", "--timeout", "2"]),
        &db,
    )
    .unwrap();
    assert_eq!(worker.join().unwrap(), ["/ab", "/c"]);
    assert_eq!(output["scope"]["all_dataset_sources_selected"], false);
    assert_eq!(output["distinct_urls"], 2);
    assert_eq!(output["snapshot"], "u1-offline-test");
    for (i, status) in ["identical_bytes", "changed_bytes", "check_failed"]
        .iter()
        .enumerate()
    {
        assert_eq!(output["results"][i]["status"], *status);
    }
    assert_eq!(output["results"][2]["http_status"], 404);
    assert!(output["results"][2].get("current_sha256").is_none());
}

#[test]
fn refuse_invalid_scopes_before_requests() {
    let db = db();
    assert!(updates::run(args(&["--source", "unknown"]), &db).is_err());
    assert!(updates::run(args(&["--dataset", "unknown"]), &db).is_err());
    assert_eq!(
        updates::run(args(&["--dataset", "empty"]), &db).unwrap()["results"],
        serde_json::json!([])
    );
    for invalid in [
        vec!["--dataset", "test", "--source", "A"],
        vec!["--source", "A", "--limit", "2"],
        vec!["--dataset", "test", "--timeout", "61"],
        vec!["--dataset", "test", "--limit", "0"],
    ] {
        assert!(Command::try_parse_from(std::iter::once("check-updates").chain(invalid)).is_err());
    }
}
