//! The ft-materials CLI. Source collection, storage, calculations and model adapters run natively.
mod cad;
mod catalog;
mod danish;
mod disassembly;
mod field_sources;
mod heating;
mod lifetable;
mod operations;
mod query;
mod reviews;
mod store;
mod thermal;
mod updates;
use anyhow::{Result, ensure};
use clap::{Parser, Subcommand};
use serde_json::{Value, json};
use std::path::PathBuf;

#[derive(Parser)]
#[command(
    name = "ft-materials",
    version,
    about = "Material data, source editions and native SolidCraft / BIMCraft adapters"
)]
struct Cli {
    /// Repository containing the checked-in Parquet and original-source supplements.
    #[arg(long, global = true, default_value = ".")]
    root: PathBuf,
    /// Local database directory (default: data/editions inside the repository).
    #[arg(long, global = true)]
    store: Option<PathBuf>,
    /// Immutable edition ID or latest. Model selections carry their own immutable edition ID.
    #[arg(long, global = true, default_value = "latest")]
    snapshot: String,
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    /// Install the complete shared foundation and activate a new immutable edition.
    Build {
        #[arg(long, conflicts_with = "supplement")]
        base_only: bool,
        #[arg(long)]
        supplement: Vec<PathBuf>,
        #[arg(long)]
        expect: Option<String>,
        #[arg(long)]
        no_activate: bool,
        #[arg(long)]
        require_originals: bool,
    },
    /// Show counts and the fingerprint of each data input.
    #[command(alias = "stats")]
    Status,
    /// Recompute the full checksums of the installed database files.
    Verify,
    /// Search Danish or source terms, an entity kind or a family.
    Search(query::Search),
    /// Read one material, its precise source versions and observations.
    #[command(alias = "show")]
    Lookup(query::Lookup),
    /// Find observations across sources by canonical ID or published property label.
    Observations(query::Observations),
    /// List canonical properties and their source-specific labels.
    Properties(query::Page),
    /// Read the Danish field catalogue, including scope, units and conditions.
    Fields(catalog::FieldsArgs),
    /// Measure documented coverage and gaps for fields, datasets or individual subjects.
    Coverage(catalog::CoverageArgs),
    /// Read sourced catalog evidence for one subject, including structured values.
    Facts(catalog::FactsArgs),
    /// Read field evidence through a checked part in SolidCraft or BIMCraft.
    ModelFacts(cad::ModelFactsArgs),
    /// Rebuild the public field-source collections from published originals.
    CollectFieldSources,
    /// Rebuild Danish heating technology scenarios from the April 2026 source workbook.
    CollectHeating,
    /// Rebuild documented institutional review records using locked ÖKOBAUDAT originals.
    CollectReviews {
        /// Download missing originals from the URLs recorded in the selected edition.
        #[arg(long)]
        fetch: bool,
    },
    /// Build the local Danish BUILD lifetime reference tables from the locked publisher workbook.
    CollectLifetimes {
        #[arg(long)]
        offline: bool,
    },
    /// Rebuild structured service-life and maintenance records from source documents.
    CollectOperations(operations::Args),
    /// Read a source original's location, rights and checksum.
    Source { id: String },
    /// Compare editions and optionally identify inputs affected in a specific model selection.
    Changes {
        before: String,
        after: String,
        #[arg(long)]
        selection: Option<PathBuf>,
    },
    /// Check current publisher response bytes for the explicitly selected sources.
    CheckUpdates(updates::Args),
    /// Regenerate the thermal and moisture data from the authors' original ZIP and workbook.
    CollectTampere(thermal::Args),
    /// Archive and decode EPD Danmark declarations locally from their original PDFs.
    CollectEpd(danish::Args),
    /// Read actual quantities from a local CAD/BIM model.
    Extract {
        model: PathBuf,
        #[arg(long, value_enum)]
        software: cad::Software,
        #[arg(long)]
        mesh_quantities: bool,
    },
    /// Apply a shared, snapshot-pinned material selection to this exact model revision.
    Assess(cad::Args),
    /// Calculate a source-bound mass, climate contribution or moisture movement from JSON.
    Calculate { request: PathBuf },
    /// Assess repair/disassembly plans and their source-bound supplied-product impacts.
    Disassembly {
        request: PathBuf,
        /// Recompute and reject a report from another request, model, edition or binary.
        #[arg(long)]
        check: Option<PathBuf>,
        /// Print a readable Danish assessment instead of the detailed JSON record.
        #[arg(long, conflicts_with = "check")]
        text: bool,
    },
    /// Normalize a quantity with an explicit dimension.
    Normalize {
        #[arg(long, allow_hyphen_values = true)]
        value: f64,
        #[arg(long)]
        unit: String,
        #[arg(long)]
        dimension: String,
    },
}
fn run(cli: Cli) -> Result<Value> {
    let root = cli.root.canonicalize()?;
    let location = cli.store.unwrap_or_else(|| root.join("data/editions"));
    let edition = || store::open(&location, &cli.snapshot);
    match cli.command {
        Command::Build {
            base_only,
            supplement,
            expect,
            no_activate,
            require_originals,
        } => {
            let folders = if base_only {
                vec![]
            } else if supplement.is_empty() {
                [
                    "tampere",
                    "operations",
                    "field-sources",
                    "ens-varme",
                    "oekobaudat-review",
                ]
                .iter()
                .map(|name| root.join("data/supplements").join(name))
                .collect()
            } else {
                supplement
            };
            store::build(
                &root,
                &location,
                &folders,
                expect.as_deref(),
                !no_activate,
                require_originals,
            )
        }
        Command::Status => Ok(edition()?.manifest),
        Command::Verify => store::verify(&edition()?),
        Command::Search(a) => query::search(&edition()?, a),
        Command::Lookup(a) => query::lookup(&edition()?, a),
        Command::Observations(a) => query::observations(&edition()?, a),
        Command::Properties(a) => query::properties(&edition()?, a),
        Command::Fields(a) => catalog::fields(a),
        Command::Coverage(a) => catalog::coverage(&edition()?, a),
        Command::Facts(a) => catalog::facts(&edition()?, a),
        Command::CollectLifetimes { offline } => lifetable::collect(&root, offline),
        Command::CollectReviews { fetch } => reviews::collect(&root, &edition()?, fetch),
        Command::CollectHeating => heating::collect(&root),
        Command::CollectFieldSources => field_sources::collect(&root),
        Command::CollectOperations(mut a) => {
            a.root = root;
            operations::run(a)
        }
        Command::ModelFacts(a) => {
            let e = pinned(&location, &cli.snapshot, &a.model.selection)?;
            cad::model_facts(a, &e)
        }
        Command::Source { id } => {
            let e = edition()?;
            let s = query::rows(
                &e.db,
                "SELECT * FROM unified_sources WHERE id=?",
                vec![id.into()],
            )?;
            ensure!(s.len() == 1, "Source not found");
            Ok(json!({"snapshot":e.id,"source":s[0]}))
        }
        Command::Changes {
            before,
            after,
            selection,
        } => query::changes(&location, &before, &after, selection.as_deref()),
        Command::CollectTampere(mut a) => {
            a.root = root;
            thermal::run(a)
        }
        Command::CollectEpd(mut a) => {
            a.root = root;
            danish::run(a)
        }
        Command::CheckUpdates(a) => updates::run(a, &edition()?.db),
        Command::Extract {
            model,
            software,
            mesh_quantities,
        } => cad::extract(&model, software, mesh_quantities),
        Command::Assess(a) => {
            let e = pinned(&location, &cli.snapshot, &a.selection)?;
            cad::run(a, &e.db, &e.id)
        }
        Command::Calculate { request } => {
            let e = edition()?;
            let mut r = cad::calculate(&e.db, &store::read(&request)?)?;
            r["snapshot"] = e.id.into();
            Ok(r)
        }
        Command::Disassembly { request, check, .. } => {
            let e = pinned(&location, &cli.snapshot, &request)?;
            let result = disassembly::run(&request, &e.db, &e.id)?;
            if let Some(report) = check {
                ensure!(
                    store::read(&report)? == result,
                    "Disassembly report is stale or changed; regenerate it"
                );
                Ok(
                    json!({"current":true,"assessment_status":result["status"],"request_sha256":result["request_sha256"],"snapshot":e.id}),
                )
            } else {
                Ok(result)
            }
        }
        Command::Normalize {
            value,
            unit,
            dimension,
        } => cad::normalize(value, &unit, &dimension),
    }
}
fn pinned(
    location: &std::path::Path,
    requested: &str,
    selection_path: &std::path::Path,
) -> Result<store::Edition> {
    let selection = store::read(selection_path)?;
    let id = store::text(&selection, "snapshot")?;
    ensure!(
        id != "latest" && (requested == "latest" || requested == id),
        "Model selection must use its pinned edition"
    );
    store::open(location, id)
}
fn main() {
    let cli = Cli::parse();
    let text = matches!(&cli.command, Command::Disassembly { text: true, .. });
    match run(cli) {
        Ok(v) => {
            if text {
                println!("{}", disassembly::render(&v));
            } else {
                println!("{}", serde_json::to_string_pretty(&v).unwrap());
            }
            if v["ok"] == false {
                std::process::exit(1)
            }
            if v["status"] == "partial" || v["status"] == "unresolved" {
                std::process::exit(2)
            }
        }
        Err(e) => {
            eprintln!("{}", json!({"error":format!("{e:#}")}));
            std::process::exit(1)
        }
    }
}
