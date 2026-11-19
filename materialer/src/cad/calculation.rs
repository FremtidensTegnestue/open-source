use anyhow::{Context, Result, bail, ensure};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::sync::LazyLock;

static UNITS: LazyLock<Value> = LazyLock::new(|| {
    serde_json::from_str(include_str!("units.json")).expect("valid bundled conversion table")
});

pub(super) fn text<'a>(row: &'a Value, field: &str) -> Result<&'a str> {
    row[field]
        .as_str()
        .filter(|s| !s.is_empty())
        .with_context(|| format!("Missing {field}"))
}
fn number(v: &Value) -> Result<f64> {
    v.as_f64()
        .filter(|n| n.is_finite())
        .context("Expected a finite number")
}
fn positive(v: f64) -> Result<f64> {
    ensure!(
        v.is_finite() && v > 0.0,
        "Expected a finite positive quantity"
    );
    Ok(v)
}
fn product(a: f64, b: f64) -> Result<f64> {
    let v = a * b;
    ensure!(v.is_finite(), "Numeric overflow");
    Ok(v)
}

pub fn normalize(value: f64, unit: &str, dimension: &str) -> Result<Value> {
    let units = &UNITS[dimension];
    let factor = units[1][unit.trim()]
        .as_f64()
        .with_context(|| format!("Unsupported unit {unit} for {dimension}"))?;
    Ok(
        json!({"value":product(value,factor)?,"unit":units[0],"dimension":dimension,"original_value":value,
              "original_unit":unit,"factor":factor,"offset":0}),
    )
}

pub(super) fn observation(db: &Connection, material: &str, id: &str) -> Result<Value> {
    let mut r = db.query_row(
        "SELECT o.dataset_id,o.property,o.property_id,o.value,o.unit,o.module,o.declared_unit,o.method,o.conditions_json,
                o.source_id,o.source_version_id,o.source_locator,o.source_url,s.sha256,s.publisher,s.license,s.license_status
         FROM unified_observations o JOIN sources s ON s.id=o.source_id WHERE o.id=?1 AND o.material_id=?2",
        params![id,material],|r| Ok(json!({"id":id,"material_id":material,"dataset_id":r.get::<_,String>(0)?,
        "property":r.get::<_,String>(1)?,"property_id":r.get::<_,String>(2)?,"value":r.get::<_,Option<f64>>(3)?,
        "unit":r.get::<_,Option<String>>(4)?,"module":r.get::<_,Option<String>>(5)?,"declared_unit":r.get::<_,Option<String>>(6)?,
        "method":r.get::<_,Option<String>>(7)?,"conditions":r.get::<_,String>(8)?,"source_id":r.get::<_,String>(9)?,
        "source_version_id":r.get::<_,String>(10)?,"source_locator":r.get::<_,String>(11)?,"source_url":r.get::<_,String>(12)?,
        "sha256":r.get::<_,String>(13)?,"publisher":r.get::<_,Option<String>>(14)?,"license":r.get::<_,Option<String>>(15)?,
        "license_status":r.get::<_,Option<String>>(16)?}))).with_context(|| format!("Observation {id} unavailable for {material}"))?;
    r["conditions"] = serde_json::from_str(text(&r, "conditions")?)?;
    Ok(r)
}

pub(super) fn mass(obs: &Value, q: &Value) -> Result<Value> {
    ensure!(
        obs["property"] == "density"
            || (obs["property"] == "gross_density"
                && obs["dataset_id"] == "environmental"
                && obs["conditions"]["reference_flow"] == true),
        "The selected observation is not a material density"
    );
    let density = normalize(number(&obs["value"])?, text(obs, "unit")?, "density")?;
    let volume = normalize(number(&q["value"])?, text(q, "unit")?, "volume")?;
    let v = number(&volume["value"])?;
    ensure!(v >= 0.0, "Negative volume");
    let kg = product(v, positive(number(&density["value"])?)?)?;
    Ok(
        json!({"status":"ok","value":kg,"unit":"kg","method":{"id":"mass.volume_density.v1"},
              "inputs":{"volume":volume,"density":obs,"density_normalized":density}}),
    )
}

pub(super) fn basis(obs: &Value) -> Result<Value> {
    let declared = text(obs, "declared_unit")?.trim();
    let parts: Vec<_> = declared.split_whitespace().collect();
    let (amount, unit) = match parts.as_slice() {
        [amount, unit] => (positive(amount.parse()?)?, *unit),
        [unit] => {
            let c = &obs["conditions"];
            let amount = positive(number(&c["declared_amount"])?)?;
            let refs = c["declared_references"]
                .as_array()
                .context("Missing declared references")?;
            let matches: Vec<_> = refs.iter().filter(|r| r["unit"] == *unit).collect();
            ensure!(
                !matches.is_empty() && matches.iter().all(|r| r["amount"].as_f64() == Some(amount)),
                "Inconsistent declared reference basis"
            );
            (amount, *unit)
        }
        _ => bail!("Unsupported declared reference basis: {declared}"),
    };
    let alias = match unit {
        "qm" | "sqm" => "m2",
        "cbm" => "m3",
        other => other,
    };
    for dim in ["mass", "volume", "area"] {
        if let Ok(mut n) = normalize(amount, alias, dim) {
            n["source_unit"] = json!(unit);
            return Ok(n);
        }
    }
    bail!("Unsupported declared unit: {unit}")
}
pub(super) fn climate(obs: &Value, q: &Value) -> Result<Value> {
    ensure!(
        matches!(
            text(obs, "property")?,
            "global_warming_potential"
                | "gwp"
                | "gwp_total"
                | "gwp_fossil"
                | "gwp_biogenic"
                | "gwp_luluc"
        ),
        "Expected a supported GWP indicator"
    );
    let factor = match text(obs, "unit")? {
        "kg CO2-eq" | "kg CO2-Equiv." | "kg CO2 eq." | "kg CO2e" | "kgCO2e" | "kg CO2-Äqv."
        | "kg CO2-eq." | "kg CO_(2) eq" | "kg CO_(2) eqv." | "kg CO_(2)-Äq." => 1.0,
        "g CO2-eq" => 0.001,
        "t CO2-eq" => 1000.0,
        other => bail!("Invalid GWP unit: {other}"),
    };
    let module = text(obs, "module")?;
    ensure!(
        obs["conditions"]["record_scope"] != "installation_area_reference_factor",
        "Installation factor requires a distinct area/year method"
    );
    let declared = basis(obs)?;
    let quantity = normalize(
        number(&q["value"])?,
        text(q, "unit")?,
        text(&declared, "dimension")?,
    )?;
    let amount = number(&quantity["value"])?;
    ensure!(amount >= 0.0, "Negative quantity");
    let ratio = amount / positive(number(&declared["value"])?)?;
    Ok(
        json!({"status":"ok","value":product(product(number(&obs["value"])?,factor)?,ratio)?,"unit":"kg CO2-eq","module":module,
        "indicator":obs["property"],"indicator_method":obs["method"],"method":{"id":"climate.declared_reference_scaling.v1"},
        "inputs":{"quantity":quantity,"source_observation":obs,"declared_basis":declared,"scaling_factor":ratio,"numerator_conversion_factor":factor}}),
    )
}
pub(super) fn moisture(obs: &Value, req: &Value) -> Result<Value> {
    let dir = text(req, "direction")?;
    ensure!(
        matches!(dir, "radial" | "tangential")
            && obs["property"] == format!("moisture_dimensional_change_coefficient_{dir}"),
        "Incompatible wood coefficient or direction"
    );
    let coeff = normalize(
        number(&obs["value"])?,
        text(obs, "unit")?,
        "moisture_coefficient",
    )?;
    let amount = positive(number(&coeff["value"])?)?;
    let q = &req["dimension"];
    let dim = normalize(number(&q["value"])?, text(q, "unit")?, "length")?;
    let start = number(&req["initial_moisture_percent"])?;
    let end = number(&req["final_moisture_percent"])?;
    let c = &obs["conditions"];
    let min = number(&c["valid_moisture_content_percent_min"])?;
    let max = number(&c["valid_moisture_content_percent_max"])?;
    ensure!(
        (min..=max).contains(&start) && (min..=max).contains(&end) && start >= 0. && end >= 0.,
        "Moisture outside source range"
    );
    let length = positive(number(&dim["value"])?)?;
    let change = product(product(length, amount)?, end - start)?;
    let final_length = length + change;
    ensure!(final_length.is_finite(), "Numeric overflow");
    Ok(
        json!({"status":"ok","value":change,"unit":"m","method":{"id":"wood.usda_2021_eq13_3.v1"},"final_dimension_m":final_length,
              "inputs":{"dimension":dim,"coefficient":obs,"coefficient_normalized":coeff,"initial_moisture_percent":start,"final_moisture_percent":end}}),
    )
}

pub fn calculate(db: &Connection, req: &Value) -> Result<Value> {
    let material = text(req, "material_id")?;
    match text(req, "kind")? {
        "mass" => mass(
            &observation(db, material, text(req, "density_observation_id")?)?,
            &req["quantity"],
        ),
        "climate" => climate(
            &observation(db, material, text(req, "gwp_observation_id")?)?,
            &req["quantity"],
        ),
        "moisture" => moisture(
            &observation(db, material, text(req, "coefficient_observation_id")?)?,
            req,
        ),
        other => bail!("Unknown calculation: {other}"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn reference_mass_uses_declared_amount_and_module() {
        let mut obs = json!({"property":"gwp_total","value":859,"unit":"kg CO_(2) eq","module":"A1","declared_unit":"kg","conditions":{"declared_amount":1000,"declared_references":[{"unit":"kg","amount":1000}]}});
        let q = json!({"value":500,"unit":"kg"});
        assert_eq!(climate(&obs, &q).unwrap()["value"], 429.5);
        obs["conditions"]["declared_references"][0]["amount"] = json!(1);
        assert!(climate(&obs, &q).is_err());
    }
    #[test]
    fn same_product_gross_density_requires_mass_unit_and_reference_flow() {
        let mut obs = json!({"dataset_id":"environmental","property":"gross_density","value":2100,"unit":"kg/m^3","conditions":{"reference_flow":true}});
        let q = json!({"value":10,"unit":"L"});
        assert_eq!(mass(&obs, &q).unwrap()["value"], 21.0);
        obs["conditions"]["reference_flow"] = json!(false);
        assert!(mass(&obs, &q).is_err());
        obs["conditions"]["reference_flow"] = json!(true);
        obs["unit"] = json!("-");
        assert!(mass(&obs, &q).is_err());
    }
    #[test]
    fn negative_valid_gwp_retained_and_wood_range_checked() {
        let obs = json!({"property":"gwp","value":-200,"unit":"kg CO2e","module":"A1-A3","declared_unit":"1 ton","conditions":{}});
        assert_eq!(
            climate(&obs, &json!({"value":500,"unit":"kg"})).unwrap()["value"],
            -100.0
        );
        let coeff = json!({"property":"moisture_dimensional_change_coefficient_tangential","value":0.00256,"unit":"1/%MC",
            "conditions":{"valid_moisture_content_percent_min":6,"valid_moisture_content_percent_max":14}});
        let mut req = json!({"direction":"tangential","initial_moisture_percent":8,"final_moisture_percent":11,"dimension":{"value":1000,"unit":"mm"}});
        assert!(
            (moisture(&coeff, &req).unwrap()["value"].as_f64().unwrap() - 0.00768).abs() < 1e-14
        );
        req["final_moisture_percent"] = json!(15);
        assert!(moisture(&coeff, &req).is_err());
        assert!(normalize(f64::MAX, "t", "mass").is_err());
    }
}
