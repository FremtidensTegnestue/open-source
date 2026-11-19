//! Explicit intervention plans. No circularity score, future reuse credit or implicit LCA.
use crate::{cad, store};
use anyhow::{Context, Result, ensure};
use rusqlite::Connection as Database;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};

#[derive(Clone, Copy, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum Action {
    Retain,
    RepairInPlace,
    TemporarilyRemove,
    Remove,
    Replace,
    Install,
}
impl Action {
    fn opens(self) -> bool {
        matches!(self, Self::TemporarilyRemove | Self::Remove | Self::Replace)
    }
    fn supplies(self) -> bool {
        matches!(self, Self::Replace | Self::Install)
    }
}
#[derive(Clone, Copy, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum Outcome {
    Reversible,
    Destructive,
    Unknown,
}
#[derive(Clone, Copy, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum Access {
    Accessible,
    Blocked,
    Unknown,
}
#[derive(Clone, Copy, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum Basis {
    Unknown,
    Assumed,
    Documented,
    Tested,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Evidence {
    basis: Basis,
    note: String,
    reference: Option<String>,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Mass {
    value_kg: f64,
    evidence: Evidence,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Joint {
    id: String,
    method: String,
    access: Access,
    outcome: Outcome,
    evidence: Evidence,
    #[serde(default)]
    requires_removal: Vec<String>,
    #[serde(default)]
    sacrificial_parts: Vec<String>,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Part {
    id: String,
    name: String,
    origin: Origin,
    initially_present: bool,
    current_mass: Option<Mass>,
    #[serde(default)]
    joints: Vec<Joint>,
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum Origin {
    Existing,
    Reused,
    New,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Quantity {
    value: f64,
    unit: String,
    evidence: Evidence,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Delivery {
    id: String,
    name: String,
    covers_parts: Vec<String>,
    material_id: Option<String>,
    quantity: Option<Quantity>,
    #[serde(default)]
    gwp_observation_ids: Vec<String>,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Variant {
    id: String,
    name: String,
    equivalence: Evidence,
    parts: Vec<Part>,
    actions: BTreeMap<String, Action>,
    deliveries: Vec<Delivery>,
    /// An explicit declaration about the supplied-product inventory, not a verified fact.
    supplied_inventory_complete: bool,
    unknowns: Vec<String>,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct FileBinding {
    path: String,
    sha256: String,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Scope {
    id: String,
    function: String,
    project_kind: ProjectKind,
    /// E.g. current repair or future pane replacement using today's product references.
    intervention: String,
    model: Option<FileBinding>,
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum ProjectKind {
    NewBuild,
    Renovation,
    Transformation,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Request {
    schema_version: u8,
    snapshot: String,
    scope: Scope,
    indicator: String,
    modules: Vec<String>,
    variants: Vec<Variant>,
    #[serde(default)]
    basis_files: Vec<FileBinding>,
}

fn named(s: &str) -> Result<()> {
    ensure!(!s.trim().is_empty(), "Empty ID or description");
    Ok(())
}
fn evidence(e: &Evidence) -> Result<()> {
    named(&e.note)?;
    if matches!(e.basis, Basis::Documented | Basis::Tested) {
        named(
            e.reference
                .as_deref()
                .context("Documented/tested evidence needs a reference")?,
        )?;
    }
    Ok(())
}
fn module_members(module: &str) -> Result<BTreeSet<String>> {
    if module == "D" {
        return Ok(BTreeSet::from(["D".into()]));
    }
    let parse = |s: &str| -> Result<(char, u8)> {
        let b = s.as_bytes();
        ensure!(
            b.len() == 2 && matches!(b[0], b'A' | b'B' | b'C'),
            "Invalid module {module}"
        );
        let n = b[1].wrapping_sub(b'0');
        let max = match b[0] {
            b'A' => 5,
            b'B' => 7,
            _ => 4,
        };
        ensure!(n > 0 && n <= max, "Invalid module {module}");
        Ok((b[0] as char, n))
    };
    let pieces = module.split('-').collect::<Vec<_>>();
    ensure!(pieces.len() <= 2, "Invalid module {module}");
    let (stage, start) = parse(pieces[0])?;
    let (end_stage, end) = parse(pieces.last().unwrap())?;
    ensure!(
        stage == end_stage && start <= end,
        "Invalid module {module}"
    );
    Ok((start..=end).map(|n| format!("{stage}{n}")).collect())
}
fn issue(issues: &mut Vec<Value>, code: &str, part: &str, note: &str) {
    let v = json!({"code":code,"part_id":part,"message":note});
    if !issues.contains(&v) {
        issues.push(v);
    }
}

/// Expand the supplied access plan; expansion proposes work, never changes a model.
fn visit<'a>(
    id: &'a str,
    parts: &BTreeMap<&'a str, &'a Part>,
    actions: &mut BTreeMap<String, Action>,
    visiting: &mut BTreeSet<String>,
    ordered: &mut Vec<String>,
    issues: &mut Vec<Value>,
) -> Result<()> {
    if ordered.iter().any(|s| s == id) {
        return Ok(());
    }
    ensure!(
        visiting.insert(id.into()),
        "Cyclic disassembly access at {id}"
    );
    let part = parts[id];
    if actions[id].opens() {
        if part.joints.is_empty() {
            issue(
                issues,
                "connection_missing",
                id,
                "Ingen beskrevet adskillelsesmetode.",
            );
        }
        for joint in &part.joints {
            for before in &joint.requires_removal {
                if matches!(actions[before], Action::Retain | Action::RepairInPlace) {
                    actions.insert(before.clone(), Action::TemporarilyRemove);
                }
                if matches!(actions[before], Action::Install) {
                    anyhow::bail!("Cannot remove initially absent access part {before}");
                }
                visit(before, parts, actions, visiting, ordered, issues)?;
            }
            for loss in &joint.sacrificial_parts {
                let action = if actions[loss] == Action::Remove {
                    Action::Remove
                } else {
                    Action::Replace
                };
                actions.insert(loss.clone(), action);
                // A collateral loss is not evidence that this part must come out first.
            }
            if joint.access != Access::Accessible {
                issue(issues, "access_unresolved", id, &joint.method);
            }
            if joint.outcome == Outcome::Unknown {
                issue(issues, "separation_unknown", id, &joint.method);
            }
            if matches!(joint.evidence.basis, Basis::Unknown | Basis::Assumed) {
                issue(issues, "separation_not_verified", id, &joint.evidence.note);
            }
            if joint.outcome == Outcome::Destructive && actions[id] == Action::TemporarilyRemove {
                actions.insert(id.into(), Action::Replace);
                issue(
                    issues,
                    "access_part_requires_replacement",
                    id,
                    "Midlertidig udtagning kan ikke forudsættes tabsfri.",
                );
            }
        }
    }
    visiting.remove(id);
    ordered.push(id.into());
    Ok(())
}

fn assess(
    v: &Variant,
    req: &Request,
    db: &Database,
    methods: &mut BTreeSet<String>,
) -> Result<Value> {
    evidence(&v.equivalence)?;
    let mut parts = BTreeMap::new();
    let mut joint_ids = BTreeSet::new();
    for p in &v.parts {
        named(&p.id)?;
        named(&p.name)?;
        ensure!(
            parts.insert(p.id.as_str(), p).is_none(),
            "Duplicate part {}",
            p.id
        );
        if let Some(m) = &p.current_mass {
            ensure!(
                m.value_kg.is_finite() && m.value_kg >= 0.,
                "Invalid mass for {}",
                p.id
            );
            ensure!(
                p.initially_present,
                "Initially absent part cannot have current mass"
            );
            evidence(&m.evidence)?;
            ensure!(
                m.evidence.basis != Basis::Unknown,
                "Numeric mass needs an explicit assumption or evidence"
            );
        }
        for j in &p.joints {
            named(&j.id)?;
            named(&j.method)?;
            evidence(&j.evidence)?;
            ensure!(joint_ids.insert(&j.id), "Duplicate connection {}", j.id);
        }
    }
    ensure!(!parts.is_empty(), "Empty part inventory");
    for p in &v.parts {
        for j in &p.joints {
            for other in j.requires_removal.iter().chain(&j.sacrificial_parts) {
                ensure!(
                    other != &p.id
                        && parts
                            .get(other.as_str())
                            .is_some_and(|p| p.initially_present),
                    "Invalid access/loss part {other}"
                );
            }
        }
    }
    let mut actions = parts
        .keys()
        .map(|p| (p.to_string(), Action::Retain))
        .collect::<BTreeMap<_, _>>();
    for (id, a) in &v.actions {
        let p = parts
            .get(id.as_str())
            .with_context(|| format!("Unknown part {id}"))?;
        ensure!(
            p.initially_present != (*a == Action::Install),
            "Action incompatible with initial presence: {id}"
        );
        actions.insert(id.clone(), *a);
    }
    ensure!(
        parts
            .values()
            .all(|p| p.initially_present || actions[&p.id] == Action::Install),
        "Initially absent parts need explicit install actions"
    );
    let mut issues = vec![];
    if matches!(v.equivalence.basis, Basis::Unknown | Basis::Assumed) {
        issue(
            &mut issues,
            "functional_equivalence_unverified",
            "",
            &v.equivalence.note,
        );
    }
    let mut order = vec![];
    // A later closure can upgrade a previously visited part; re-evaluate until stable.
    loop {
        let before = actions.clone();
        order.clear();
        for id in parts.keys() {
            visit(
                id,
                &parts,
                &mut actions,
                &mut BTreeSet::new(),
                &mut order,
                &mut issues,
            )?;
        }
        if before == actions {
            break;
        }
    }
    let mut missing_mass = vec![];
    let (mut retained, mut removed) = (0., 0.);
    for p in &v.parts {
        if p.initially_present {
            if let Some(m) = &p.current_mass {
                if matches!(actions[&p.id], Action::Remove | Action::Replace) {
                    removed += m.value_kg;
                } else {
                    retained += m.value_kg;
                }
            } else {
                missing_mass.push(p.id.clone());
            }
        }
    }
    ensure!(retained.is_finite() && removed.is_finite(), "Mass overflow");
    let fraction = if missing_mass.is_empty() && retained + removed > 0. {
        Some(retained / (retained + removed))
    } else {
        None
    };
    let mut covered = BTreeSet::new();
    let mut delivery_ids = BTreeSet::new();
    let mut totals = BTreeMap::<String, f64>::new();
    let mut coverage = BTreeMap::<String, usize>::new();
    let mut results = vec![];
    let mut product_complete = v.supplied_inventory_complete;
    if !product_complete {
        issue(
            &mut issues,
            "product_inventory_open",
            "",
            "Tilførte produkter er ikke fuldt registreret.",
        );
    }
    for d in &v.deliveries {
        named(&d.id)?;
        named(&d.name)?;
        ensure!(delivery_ids.insert(&d.id), "Duplicate delivery {}", d.id);
        ensure!(
            !d.covers_parts.is_empty(),
            "Delivery {} needs product coverage",
            d.id
        );
        for part in &d.covers_parts {
            ensure!(
                parts.contains_key(part.as_str()) && actions[part] != Action::Retain,
                "Delivery covers absent or untouched part {part}"
            );
            ensure!(
                covered.insert(part.clone()),
                "Overlapping whole-product/component coverage: {part}"
            );
        }
        if let Some(q) = &d.quantity {
            ensure!(
                q.value.is_finite() && q.value > 0.,
                "Supplied quantity must be positive"
            );
            named(&q.unit)?;
            evidence(&q.evidence)?;
            ensure!(
                q.evidence.basis != Basis::Unknown,
                "Numeric quantity needs an explicit assumption or evidence"
            );
        }
        let mut reported = BTreeMap::new();
        let mut module_set = BTreeSet::new();
        let mut calculations = vec![];
        if let (Some(material), Some(q)) = (&d.material_id, &d.quantity) {
            named(material)?;
            for oid in &d.gwp_observation_ids {
                let r = cad::calculate(
                    db,
                    &json!({"kind":"climate","material_id":material,"gwp_observation_id":oid,"quantity":{"value":q.value,"unit":q.unit}}),
                )?;
                ensure!(
                    r["indicator"] == req.indicator,
                    "Incompatible climate indicator in {}",
                    d.id
                );
                methods.insert(serde_json::to_string(&r["indicator_method"])?);
                if r["indicator_method"].is_null() || r["indicator_method"] == "" {
                    issue(
                        &mut issues,
                        "climate_method_not_reported",
                        &d.id,
                        "Kildens metodefelt er tomt; ingen automatisk variantdifference.",
                    );
                }
                let module = r["module"].as_str().context("Missing result module")?;
                for member in module_members(module)? {
                    ensure!(
                        module_set.insert(member),
                        "Overlapping declared modules in {}",
                        d.id
                    );
                }
                let n = r["value"].as_f64().context("Non-numeric result")?;
                reported.insert(module.to_owned(), n);
                if req.modules.iter().any(|s| s == module) || module == "D" {
                    *totals.entry(module.into()).or_default() += n;
                }
                calculations.push(r);
            }
        }
        let missing = req
            .modules
            .iter()
            .filter(|m| !reported.contains_key(*m))
            .collect::<Vec<_>>();
        for m in &req.modules {
            if reported.contains_key(m) {
                *coverage.entry(m.clone()).or_default() += 1;
            }
        }
        if !missing.is_empty() {
            product_complete = false;
            issue(
                &mut issues,
                "product_data_missing",
                &d.id,
                "Mængde, kilde eller krævede moduler mangler. Ukendt er ikke nul.",
            );
        }
        results.push(json!({"delivery":d,"reported_modules":reported,"missing_modules":missing,"calculations":calculations}));
    }
    for (id, a) in &actions {
        if a.supplies() && !covered.contains(id) {
            product_complete = false;
            issue(
                &mut issues,
                "replacement_product_missing",
                id,
                "Nødvendig tilførsel mangler mængde/kildekobling.",
            );
        }
    }
    ensure!(totals.values().all(|v| v.is_finite()), "Climate overflow");
    let total = if product_complete {
        Some(
            req.modules
                .iter()
                .map(|m| totals.get(m).copied().unwrap_or(0.))
                .sum::<f64>(),
        )
    } else {
        None
    };
    ensure!(total.is_none_or(f64::is_finite), "Climate total overflow");
    for note in &v.unknowns {
        named(note)?;
        issue(&mut issues, "declared_unknown", "", note);
    }
    let follow_on = actions
        .iter()
        .filter(|(id, a)| v.actions.get(*id).copied().unwrap_or(Action::Retain) != **a)
        .map(|(id, a)| json!({"part_id":id,"proposed_action":a}))
        .collect::<Vec<_>>();
    let operations = order
        .iter()
        .filter(|id| actions[*id].opens())
        .map(|id| json!({"part_id":id,"action":actions[id],"joints":parts[id.as_str()].joints}))
        .collect::<Vec<_>>();
    let access_requirements = parts
        .iter()
        .filter(|(_, part)| actions[&part.id].opens())
        .map(|(id, p)| {
            let before = p
                .joints
                .iter()
                .flat_map(|j| j.requires_removal.iter())
                .collect::<BTreeSet<_>>();
            (id.to_string(), before)
        })
        .collect::<BTreeMap<_, _>>();
    let module_totals = req
        .modules
        .iter()
        .map(|m| {
            let value = if v.deliveries.is_empty() && product_complete {
                Some(0.)
            } else {
                totals.get(m).copied()
            };
            (m.clone(), json!(value))
        })
        .collect::<BTreeMap<_, _>>();
    let module_coverage=req.modules.iter().map(|m|(m.clone(),json!({"calculated_deliveries":coverage.get(m).copied().unwrap_or(0),"declared_deliveries":v.deliveries.len()}))).collect::<BTreeMap<_,_>>();
    Ok(
        json!({"id":v.id,"name":v.name,"equivalence":v.equivalence,"parts":v.parts,"requested_actions":v.actions,
        "proposed_actions":actions,"follow_on_work":follow_on,"disassembly_order":operations,"access_requirements":access_requirements,
        "mass":{"known_retained_kg":retained,"known_removed_kg":removed,"unknown_part_ids":missing_mass,
            "scenario_retained_fraction":fraction,"basis":"declared current part masses; not an independently verified reuse percentage"},
        "products":{"inventory_declared_complete":v.supplied_inventory_complete,"data_complete":product_complete,
            "known_totals_by_module":module_totals,"coverage_by_module":module_coverage,
            "D_separate":totals.get("D"),"total_for_requested_modules":total,"deliveries":results},
        "complete_lifecycle_total":null,"issues":issues}),
    )
}

pub fn run(path: &Path, db: &Database, snapshot: &str) -> Result<Value> {
    let bytes = fs::read(path)?;
    let req: Request = serde_json::from_slice(&bytes).context("Invalid disassembly request")?;
    ensure!(
        req.schema_version == 1 && req.snapshot == snapshot && req.snapshot != "latest",
        "Invalid schema or unpinned edition"
    );
    named(&req.scope.id)?;
    named(&req.scope.function)?;
    named(&req.scope.intervention)?;
    named(&req.indicator)?;
    ensure!(
        !req.modules.is_empty() && !req.variants.is_empty(),
        "Modules and variants are required"
    );
    let mut members = BTreeSet::new();
    for m in &req.modules {
        ensure!(m != "D", "Module D must stay outside the product total");
        for member in module_members(m)? {
            ensure!(members.insert(member), "Overlapping requested modules");
        }
    }
    if let Some(model) = &req.scope.model {
        let p = path.parent().unwrap_or(Path::new(".")).join(&model.path);
        ensure!(
            store::hash(&fs::read(&p)?) == model.sha256,
            "Model changed; disassembly assessment is stale"
        );
    }
    for input in &req.basis_files {
        let p = path.parent().unwrap_or(Path::new(".")).join(&input.path);
        ensure!(
            store::hash(&fs::read(&p)?) == input.sha256,
            "Evidence input changed; disassembly assessment is stale"
        );
    }
    let mut variants = vec![];
    let mut ids = BTreeSet::new();
    let mut methods = BTreeSet::new();
    let scope_ids = req.variants[0]
        .parts
        .iter()
        .map(|p| p.id.as_str())
        .collect::<BTreeSet<_>>();
    let presence = req.variants[0]
        .parts
        .iter()
        .map(|p| (p.id.as_str(), p.initially_present))
        .collect::<BTreeMap<_, _>>();
    for v in &req.variants {
        named(&v.id)?;
        named(&v.name)?;
        ensure!(ids.insert(&v.id), "Duplicate variant {}", v.id);
        ensure!(
            v.parts
                .iter()
                .map(|p| p.id.as_str())
                .collect::<BTreeSet<_>>()
                == scope_ids,
            "Variant part inventory changed; compare the same scope"
        );
        ensure!(
            v.parts
                .iter()
                .all(|p| presence[p.id.as_str()] == p.initially_present),
            "Variant initial inventory boundary changed"
        );
        variants.push(assess(v, &req, db, &mut methods)?);
    }
    ensure!(
        methods.len() <= 1,
        "Incompatible climate methods; do not combine declarations"
    );
    let reference = &variants[0];
    let comparison=variants.iter().map(|v| {
        let comparable=reference["products"]["data_complete"]==true && v["products"]["data_complete"]==true
            && reference["equivalence"]["basis"]!="unknown" && v["equivalence"]["basis"]!="unknown"
            && !methods.contains("null") && !methods.contains("\"\"");
        let delta=if comparable { Some(v["products"]["total_for_requested_modules"].as_f64().unwrap()-reference["products"]["total_for_requested_modules"].as_f64().unwrap()) } else {None};
        json!({"variant_id":v["id"],"reference_variant_id":reference["id"],"supplied_products_delta_kg_CO2e":delta,
            "basis":"conditional supplied-product reference only; excludes intervention processes, operational energy and future generations"})
    }).collect::<Vec<_>>();
    let partial = variants
        .iter()
        .any(|v| !v["issues"].as_array().unwrap().is_empty());
    Ok(
        json!({"schema_version":1,"status":if partial {"partial"} else {"ok"},"method":"disassembly.intervention.v1",
        "request_sha256":store::hash(&bytes),"snapshot":snapshot,"scope":req.scope,"indicator":req.indicator,"modules":req.modules,
        "engine_binary_sha256":store::hash(&fs::read(std::env::current_exe()?)?),
        "variants":variants,"comparison":comparison,"winner":null,"basis_files":req.basis_files,
        "limits":["Proposed plans, not technical approval or a physical disassembly test.",
            "Declared masses and evidence are not independently verified by this command.",
            "Product GWP is calculated by the existing native source-bound calculator. D is separate.",
            "No complete building LCA, future reuse credit or weighted circularity score.",
            "A file hash binds a saved model, not live selection or a supported plugin panel."]}),
    )
}

/// Human-facing view of the same assessment; it never substitutes zero for missing data.
pub fn render(report: &Value) -> String {
    fn amount(v: &Value) -> String {
        v.as_f64()
            .map(|n| format!("{n:.3} kg CO2e"))
            .unwrap_or_else(|| "ukendt".into())
    }
    let mut lines=vec!["Reparation og adskillelse".to_string(),report["scope"]["function"].as_str().unwrap_or("").into(),
        report["scope"]["intervention"].as_str().unwrap_or("").into(),
        "Forslag baseret på de angivne oplysninger; ingen fysisk afprøvning eller teknisk godkendelse.".into()];
    for variant in report["variants"].as_array().unwrap() {
        lines.push(format!("\n{}", variant["name"].as_str().unwrap()));
        let names = variant["parts"]
            .as_array()
            .unwrap()
            .iter()
            .map(|p| (p["id"].as_str().unwrap(), p["name"].as_str().unwrap()))
            .collect::<BTreeMap<_, _>>();
        for (action, label) in [
            ("retain", "Foreslås bevaret"),
            ("repair_in_place", "Repareres på stedet"),
            ("temporarily_remove", "Tages midlertidigt af"),
            ("replace", "Foreslås udskiftet"),
            ("remove", "Fjernes"),
            ("install", "Tilføjes"),
        ] {
            let parts = variant["proposed_actions"]
                .as_object()
                .unwrap()
                .iter()
                .filter(|(_, a)| *a == action)
                .map(|(id, _)| names[id.as_str()])
                .collect::<Vec<_>>();
            if !parts.is_empty() {
                lines.push(format!("{label}: {}", parts.join(", ")));
            }
        }
        if let Some(fraction) = variant["mass"]["scenario_retained_fraction"].as_f64() {
            lines.push(format!(
                "Bevaret andel i det angivne massescenarie: {:.1} % (ikke uafhængigt eftervist).",
                fraction * 100.
            ));
        } else {
            lines.push("Bevaret masseandel: ukendt.".into());
        }
        for module in report["modules"].as_array().unwrap() {
            let key = module.as_str().unwrap();
            lines.push(format!(
                "Kendt produktdelsum {key}: {}",
                amount(&variant["products"]["known_totals_by_module"][key])
            ));
        }
        lines.push(format!(
            "Tilførte produkter, samlet for de valgte moduler: {}",
            amount(&variant["products"]["total_for_requested_modules"])
        ));
        lines.push(format!(
            "Modul D, særskilt og uden for summen: {}",
            amount(&variant["products"]["D_separate"])
        ));
        let operations = variant["disassembly_order"].as_array().unwrap();
        if !operations.is_empty() {
            lines.push(
                "Foreslået adgangsplan — ikke en komplet montage- eller sikkerhedsplan:".into(),
            );
            for (i, step) in operations.iter().enumerate() {
                lines.push(format!(
                    "  {}. {}",
                    i + 1,
                    names[step["part_id"].as_str().unwrap()]
                ));
            }
        }
        for item in variant["issues"].as_array().unwrap() {
            let part = item["part_id"].as_str().unwrap();
            let label = names.get(part).copied().unwrap_or(part);
            lines.push(format!(
                "Afklaring{}: {}",
                if label.is_empty() {
                    String::new()
                } else {
                    format!(" ({label})")
                },
                item["message"].as_str().unwrap()
            ));
        }
    }
    lines.push("\nSamlet livscyklusklima: ikke beregnet. Ingen automatisk vinder eller fremtidig genbrugskredit.".into());
    lines.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    fn db() -> Database {
        let db = Database::open_in_memory().unwrap();
        db.execute_batch("CREATE TABLE sources(id TEXT,sha256 TEXT,publisher TEXT,license TEXT,license_status TEXT);
          INSERT INTO sources VALUES('source','original-hash','fixture','fixture','verified');
          CREATE TABLE unified_observations(id TEXT,material_id TEXT,dataset_id TEXT,property TEXT,property_id TEXT,
          value REAL,unit TEXT,module TEXT,declared_unit TEXT,method TEXT,conditions_json TEXT,source_id TEXT,
          source_version_id TEXT,source_locator TEXT,source_url TEXT);").unwrap();
        for (id, module, value) in [
            ("a", "A1-A3", 2.),
            ("c3", "C3", 3.),
            ("c4", "C4", 0.5),
            ("d", "D", -4.),
        ] {
            db.execute("INSERT INTO unified_observations VALUES(?1,'material','fixture','gwp_total','gwp_total',?2,'kg CO2e',?3,'1 kg','same-method','{}','source','version','table/cell','https://example.invalid/source')",rusqlite::params![id,value,module]).unwrap();
        }
        db
    }
    fn ev() -> Value {
        json!({"basis":"documented","note":"Test fixture only","reference":"fixture/section"})
    }
    fn joint(id: &str) -> Value {
        json!({"id":id,"method":"Explicit test method","access":"accessible","outcome":"reversible","evidence":ev()})
    }
    fn part(id: &str, mass: f64) -> Value {
        json!({"id":id,"name":id,"origin":"existing","initially_present":true,
          "current_mass":{"value_kg":mass,"evidence":ev()},"joints":[joint(&format!("{id}-joint"))]})
    }
    fn delivery(id: &str, kg: f64) -> Value {
        json!({"id":id,"name":id,"covers_parts":[id],"material_id":"material",
          "quantity":{"value":kg,"unit":"kg","evidence":ev()},"gwp_observation_ids":["a","c3","c4","d"]})
    }
    fn request() -> Value {
        let mut pane = part("pane", 20.);
        pane["joints"][0]["requires_removal"] = json!(["bead"]);
        pane["joints"][0]["sacrificial_parts"] = json!(["seal"]);
        let mut seal = part("seal", 0.1);
        seal["joints"][0]["outcome"] = json!("destructive");
        json!({"schema_version":1,"snapshot":"edition","scope":{"id":"window","function":"Same window service",
          "project_kind":"new_build","intervention":"Single future pane intervention with current product references","model":null},
          "indicator":"gwp_total","modules":["A1-A3","C3","C4"],"variants":[{"id":"first","name":"first","equivalence":ev(),
          "parts":[part("frame",10.),pane,part("bead",1.),seal],"actions":{"pane":"replace"},
          "deliveries":[delivery("pane",1.),delivery("seal",0.1)],"supplied_inventory_complete":true,"unknowns":[]}]})
    }
    fn run_request(req: &Value, db: &Database) -> Result<Value> {
        let dir = tempfile::tempdir()?;
        let path = dir.path().join("request.json");
        fs::write(&path, serde_json::to_vec(req)?)?;
        run(&path, db, "edition")
    }
    #[test]
    fn access_plan_expands_losses_and_uses_native_product_factors_without_d_credit() {
        let r = run_request(&request(), &db()).unwrap();
        let v = &r["variants"][0];
        assert_eq!(v["proposed_actions"]["bead"], "temporarily_remove");
        assert_eq!(v["proposed_actions"]["seal"], "replace");
        let order = v["disassembly_order"]
            .as_array()
            .unwrap()
            .iter()
            .map(|s| s["part_id"].as_str().unwrap())
            .collect::<Vec<_>>();
        assert!(order.iter().position(|s| *s == "bead") < order.iter().position(|s| *s == "pane"));
        assert_eq!(v["access_requirements"]["pane"], json!(["bead"]));
        assert!(
            (v["products"]["total_for_requested_modules"]
                .as_f64()
                .unwrap()
                - 6.05)
                .abs()
                < 1e-10
        );
        assert!((v["products"]["D_separate"].as_f64().unwrap() + 4.4).abs() < 1e-10);
        assert_eq!(
            v["products"]["deliveries"][0]["calculations"][0]["inputs"]["source_observation"]["source_id"],
            "source"
        );
        assert!(
            (v["mass"]["scenario_retained_fraction"].as_f64().unwrap() - 11. / 31.1).abs() < 1e-10
        );
        assert!(r["winner"].is_null());
        assert!(v["complete_lifecycle_total"].is_null());
    }
    #[test]
    fn unknown_mass_and_uncovered_follow_on_product_never_become_complete() {
        let mut req = request();
        req["variants"][0]["parts"][0]["current_mass"] = Value::Null;
        req["variants"][0]["deliveries"] = json!([delivery("pane", 1.)]);
        let r = run_request(&req, &db()).unwrap();
        let v = &r["variants"][0];
        assert!(v["mass"]["scenario_retained_fraction"].is_null());
        assert!(v["products"]["total_for_requested_modules"].is_null());
        assert!(r["comparison"][0]["supplied_products_delta_kg_CO2e"].is_null());
        assert_eq!(r["status"], "partial");
        let text = render(&r);
        assert!(text.contains("Bevaret masseandel: ukendt"));
        assert!(text.contains("samlet for de valgte moduler: ukendt"));
    }
    #[test]
    fn grouped_source_modules_are_not_invented_as_separate_c3_c4() {
        let db = db();
        db.execute(
            "UPDATE unified_observations SET module='C1-C4' WHERE id='c3'",
            [],
        )
        .unwrap();
        let mut req = request();
        for d in req["variants"][0]["deliveries"].as_array_mut().unwrap() {
            d["gwp_observation_ids"] = json!(["a", "c3", "d"]);
        }
        let r = run_request(&req, &db).unwrap();
        assert_eq!(
            r["variants"][0]["products"]["deliveries"][0]["missing_modules"],
            json!(["C3", "C4"])
        );
        assert!(r["variants"][0]["products"]["total_for_requested_modules"].is_null());
        assert!(r["variants"][0]["products"]["known_totals_by_module"]["C3"].is_null());
        assert!(r["variants"][0]["products"]["known_totals_by_module"]["C4"].is_null());
    }
    #[test]
    fn changed_scope_duplicate_parts_and_overlapping_product_coverage_are_rejected() {
        let mut req = request();
        let mut v = req["variants"][0].clone();
        v["id"] = json!("second");
        v["parts"].as_array_mut().unwrap().pop();
        req["variants"].as_array_mut().unwrap().push(v);
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        let p = req["variants"][0]["parts"][0].clone();
        req["variants"][0]["parts"].as_array_mut().unwrap().push(p);
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["variants"][0]["deliveries"][0]["covers_parts"] = json!(["pane", "seal"]);
        assert!(run_request(&req, &db()).is_err());
    }
    #[test]
    fn access_cycle_is_rejected_even_when_an_access_part_was_initially_retained() {
        let mut req = request();
        req["variants"][0]["parts"][2]["joints"][0]["requires_removal"] = json!(["pane"]);
        assert!(
            run_request(&req, &db())
                .unwrap_err()
                .to_string()
                .contains("Cyclic")
        );
    }
    #[test]
    fn destructive_access_creates_a_replacement_gap_and_unknown_release_stays_open() {
        let mut req = request();
        req["variants"][0]["parts"][2]["joints"][0]["outcome"] = json!("destructive");
        let r = run_request(&req, &db()).unwrap();
        assert_eq!(r["variants"][0]["proposed_actions"]["bead"], "replace");
        assert_eq!(r["variants"][0]["products"]["data_complete"], false);
        req["variants"][0]["parts"][2]["joints"][0]["outcome"] = json!("unknown");
        assert_eq!(run_request(&req, &db()).unwrap()["status"], "partial");
    }
    #[test]
    fn wrong_quantity_source_indicator_and_overlapping_modules_fail_without_fallback() {
        let mut req = request();
        req["variants"][0]["deliveries"][0]["quantity"]["unit"] = json!("m2");
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["variants"][0]["deliveries"][0]["material_id"] = json!("other-material");
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["indicator"] = json!("gwp_fossil");
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["modules"] = json!(["A1-A3", "A1"]);
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["modules"] = json!(["A1-A3", "D"]);
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["variants"][0]["deliveries"][0]["quantity"]["value"] = json!(0);
        assert!(run_request(&req, &db()).is_err());
    }
    #[test]
    fn compatible_product_comparison_is_explicitly_not_a_whole_lifecycle_winner() {
        let mut req = request();
        let mut second = req["variants"][0].clone();
        second["id"] = json!("second");
        second["deliveries"][0]["quantity"]["value"] = json!(2.);
        req["variants"].as_array_mut().unwrap().push(second);
        let r = run_request(&req, &db()).unwrap();
        assert!(
            (r["comparison"][1]["supplied_products_delta_kg_CO2e"]
                .as_f64()
                .unwrap()
                - 5.5)
                .abs()
                < 1e-10
        );
        assert!(r["winner"].is_null());
        req["variants"][1]["equivalence"]["basis"] = json!("unknown");
        assert!(
            run_request(&req, &db()).unwrap()["comparison"][1]["supplied_products_delta_kg_CO2e"]
                .is_null()
        );
    }
    #[test]
    fn saved_model_change_invalidates_assessment_and_pinned_input_is_required() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("input.json");
        let model = dir.path().join("model.sc");
        fs::write(&model, "first").unwrap();
        let mut req = request();
        req["scope"]["model"] = json!({"path":"model.sc","sha256":store::hash(b"first")});
        fs::write(&path, serde_json::to_vec(&req).unwrap()).unwrap();
        assert!(run(&path, &db(), "edition").is_ok());
        fs::write(&model, "second").unwrap();
        assert!(
            run(&path, &db(), "edition")
                .unwrap_err()
                .to_string()
                .contains("stale")
        );
        req["snapshot"] = json!("latest");
        assert!(run_request(&req, &db()).is_err());
        let mut req = request();
        req["variants"][0]["suplied_inventory_complete"] = json!(true);
        assert!(run_request(&req, &db()).is_err());
    }

    #[test]
    fn missing_method_blocks_comparison_and_different_methods_fail() {
        let database = db();
        database
            .execute("UPDATE unified_observations SET method=NULL", [])
            .unwrap();
        let r = run_request(&request(), &database).unwrap();
        assert_eq!(r["status"], "partial");
        assert!(r["comparison"][0]["supplied_products_delta_kg_CO2e"].is_null());
        database
            .execute(
                "UPDATE unified_observations SET method='other' WHERE id='a'",
                [],
            )
            .unwrap();
        assert!(run_request(&request(), &database).is_err());
    }

    #[test]
    fn source_negative_values_survive_and_evidence_file_changes_are_rejected() {
        let database = db();
        database
            .execute("UPDATE unified_observations SET value=-2 WHERE id='a'", [])
            .unwrap();
        let r = run_request(&request(), &database).unwrap();
        assert!(
            (r["variants"][0]["products"]["known_totals_by_module"]["A1-A3"]
                .as_f64()
                .unwrap()
                + 2.2)
                .abs()
                < 1e-10
        );
        let dir = tempfile::tempdir().unwrap();
        let file = dir.path().join("survey.json");
        fs::write(&file, "first").unwrap();
        let mut req = request();
        req["basis_files"] = json!([{"path":file,"sha256":store::hash(b"first")}]);
        assert!(run_request(&req, &database).is_ok());
        fs::write(&file, "changed").unwrap();
        assert!(
            run_request(&req, &database)
                .unwrap_err()
                .to_string()
                .contains("stale")
        );
    }
}
