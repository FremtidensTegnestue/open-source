//! Danish material field dictionary and evidence queries for an immutable edition.
use crate::store::{self, Edition};
use anyhow::{Result, ensure};
use clap::Args;
use serde::Serialize;
use serde_json::{Value, json};
use std::{collections::HashMap, sync::LazyLock};

mod evidence;
mod report;

const DICTIONARY: &str = include_str!("../docs/MATERIALEFELTER.tsv");
const MAPPINGS: &str = include_str!("../data/unified/field-mappings.tsv");

#[derive(Serialize)]
struct Field {
    group: &'static str,
    field_id: &'static str,
    name_da: &'static str,
    applies_to: &'static str,
    value_type: &'static str,
    unit_or_basis: &'static str,
    definition: &'static str,
    scope: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    mapping_note_da: Option<&'static str>,
}

static FIELDS: LazyLock<Vec<Field>> = LazyLock::new(|| {
    DICTIONARY
        .lines()
        .skip(1)
        .map(|line| {
            let parts: Vec<_> = line.split('\t').collect();
            let [
                group,
                field_id,
                name_da,
                applies_to,
                value_type,
                unit_or_basis,
                definition,
            ] = parts[..]
            else {
                panic!("Invalid field dictionary row: {line}");
            };
            let scope = match field_id {
                "model_binding" | "model_quantity" | "material_selection" | "derived_result"
                | "installed_identity" | "service_event" | "study_period" => "project",
                "condition_grade"
                | "remaining_service_life"
                | "hazardous_substance_survey"
                | "life_cycle_cost"
                | "reuse_evidence"
                | "service_exposure"
                | "installation_conditions"
                | "transport_scenario" => "source_or_project",
                _ => "source_or_catalogue",
            };
            let mapping_note_da = match field_id {
                "production_origin"=>Some("Oprindelsen kræver en kilde til råstoffet eller fremstillingsstedet. En EPDs markedsområde og en prøves undersøgelsesland er særskilte oplysninger."),
                "liquid_moisture_diffusivity"=>Some("EnergyPlus angiver væsketransport ved opsugning og omfordeling i m²/s som funktion af vandindhold. Tampere betegner sine kurver som moisture diffusivity uden en entydig afgrænsning til væskefasen."),
                "statistical_basis"=>Some("ENS angiver centrale, nedre og øvre scenarieestimater. NIST angiver usikkerhed på en måleværdi med type og enhed. Betydningen følger den enkelte kilde."),
                "verification"=>Some("Ved identiske værdier i Tamperes JSON og regneark henviser observationen til de sammenholdte celler. Kildens kontrolmetode følger det enkelte udsagn."),
                "layer_sequence"=>Some("En delvis lagbeskrivelse kan fastlægge den synlige side og enkelte lag. Hele opbygningen kræver dokumentation for de resterende lag."),
                _=>None
            };
            Field {
                group,
                field_id,
                name_da,
                applies_to,
                value_type,
                unit_or_basis,
                definition,
                scope,
                mapping_note_da,
            }
        })
        .collect()
});

static INDEX: LazyLock<HashMap<&'static str, usize>> = LazyLock::new(|| {
    FIELDS
        .iter()
        .enumerate()
        .map(|(i, f)| (f.field_id, i))
        .collect()
});

static ALIASES: LazyLock<HashMap<(&'static str, &'static str), &'static str>> =
    LazyLock::new(|| {
        let mut map = HashMap::new();
        for line in MAPPINGS.lines().skip(1) {
            let fields = line.split('\t').collect::<Vec<_>>();
            let [dataset, field, names] = fields[..] else {
                panic!("Invalid field mapping: {line}")
            };
            assert!(is_known(field));
            for name in names.split_whitespace() {
                assert!(map.insert((dataset, name), field).is_none());
            }
        }
        map
    });

pub fn is_known(id: &str) -> bool {
    INDEX.contains_key(id)
}

/// Includes executable projection rules as well as the dictionary and reviewed aliases.
pub fn fingerprint() -> String {
    store::hash(
        concat!(
            include_str!("../docs/MATERIALEFELTER.tsv"),
            "\0",
            include_str!("../data/unified/field-mappings.tsv"),
            "\0",
            include_str!("catalog/evidence.rs"),
            "\0",
            include_str!("catalog/report.rs"),
            "\0",
            include_str!("catalog.rs")
        )
        .as_bytes(),
    )
}

#[derive(Args)]
pub struct FieldsArgs {
    /// One stable dictionary field ID
    field: Option<String>,
    /// Exact Danish group name
    #[arg(long)]
    group: Option<String>,
}

#[derive(Args)]
pub struct CoverageArgs {
    /// Limit the denominator to one exact material ID
    #[arg(long)]
    material: Option<String>,
    /// Show one dictionary field
    #[arg(long)]
    field: Option<String>,
    /// Limit the denominator to materials in one dataset
    #[arg(long)]
    dataset: Option<String>,
}

#[derive(Args)]
pub struct FactsArgs {
    /// Exact, source-specific material ID
    material: String,
    /// Only return evidence for this dictionary field
    #[arg(long)]
    field: Option<String>,
    #[arg(long, default_value_t = 50)]
    limit: usize,
    #[arg(long, default_value_t = 0)]
    offset: usize,
}

fn validate(field: Option<&str>) -> Result<()> {
    if let Some(id) = field {
        ensure!(is_known(id), "Unknown field ID: {id}");
    }
    Ok(())
}

pub fn fields(a: FieldsArgs) -> Result<Value> {
    validate(a.field.as_deref())?;
    if let Some(g) = &a.group {
        ensure!(FIELDS.iter().any(|f| f.group == g), "Unknown group: {g}");
    }
    let out: Vec<_> = FIELDS
        .iter()
        .filter(|f| {
            a.field.as_deref().is_none_or(|x| f.field_id == x)
                && a.group.as_deref().is_none_or(|g| f.group == g)
        })
        .collect();
    Ok(json!({"catalog_sha256":fingerprint(),"count":out.len(),"fields":out}))
}

pub fn coverage(e: &Edition, a: CoverageArgs) -> Result<Value> {
    validate(a.field.as_deref())?;
    report::coverage(
        e,
        a.material.as_deref(),
        a.dataset.as_deref(),
        a.field.as_deref(),
    )
}
pub fn facts(e: &Edition, a: FactsArgs) -> Result<Value> {
    material_facts(e, &a.material, a.field.as_deref(), a.limit, a.offset)
}
pub fn material_facts(
    e: &Edition,
    material: &str,
    field: Option<&str>,
    limit: usize,
    offset: usize,
) -> Result<Value> {
    validate(field)?;
    ensure!(
        (1..=10000).contains(&limit),
        "Limit must be between 1 and 10000"
    );
    report::facts(e, material, field, limit, offset)
}
