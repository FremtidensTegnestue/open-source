//! Statements scoped to the specific GFRC panel/assembly in Lindner EPD 22566.
use super::{Facts, SCENARIO, amount, conditions, confirm, pdf_text, place};
use anyhow::Result;
use serde_json::json;

pub(super) fn extract(facts: &mut Facts, doc: &pdf_extract::Document) -> Result<()> {
    let entry = facts.entry;
    let page = 4;
    let text = pdf_text(doc, page)?;
    for (group, pattern, inclusive, source) in [
        (
            "calculated-facade-life",
            r"durationofmorethan([0-9]+)years",
            false,
            "manufacturer calculated duration",
        ),
        (
            "bbsr-minimum",
            r"minimumof([0-9]+)yearsaccordingtothebbsr",
            true,
            "BBSR table 335 211, issue 02/2017 as cited by the EPD",
        ),
    ] {
        let value = amount(&text, pattern)?;
        let mut c = conditions(group, &entry.component, SCENARIO);
        c["method"] = json!(source);
        facts.life(
            json!({"lower_bound":value,"lower_inclusive":inclusive}),
            &place(page, "Reference service life"),
            &c,
        );
    }
    let loc = place(
        4,
        "Declaration regarding the use of hazardous substances, item 1",
    );
    confirm(&text, "candidate list (date: 27.06.2024)")?;
    confirm(&text, "exceeding 0.1 percentage by mass: No")?;
    let limit = amount(&text, r"exceeding([0-9]+\.[0-9]+)percentagebymass:no")?;
    let mut c = conditions(
        "candidate-list-declaration",
        &entry.component,
        "manufacturer_statement_in_epd",
    );
    c["candidate_list_date"] = json!("2024-06-27");
    c["scope"] = json!("article and component articles; applies per listed substance");
    facts.put(
        "chemical_constituent",
        json!({"group":"REACH candidate-list SVHC","upper_bound":limit,"upper_inclusive":true}),
        Some("mass-%"),
        &loc,
        &c,
    );

    let text = pdf_text(doc, 3)?;
    let loc = place(3, "Constructional data, Sound absorption");
    confirm(&text, "perforated panel with 14 % open")?;
    confirm(&text, "area and mineral wool backing")?;
    let aw = amount(&text, r"uptoαw=([0-9]+)and")?;
    let nrc = amount(&text, r"nrc=([0-9]+)area")?;
    for (group, metric, bound) in [
        ("weighted-sound-absorption", "αw", aw),
        ("noise-reduction-coefficient", "NRC", nrc),
    ] {
        let mut c = conditions(
            group,
            "perforated LinCrete panel with mineral wool backing",
            "technical_performance_in_epd",
        );
        c["open_area_percent"] = json!(14);
        c["metric"] = json!(metric);
        facts.put(
            "sound_absorption_coefficient",
            json!({"upper_bound":bound,"upper_inclusive":true}),
            Some("%"),
            &loc,
            &c,
        );
    }
    let c = conditions(
        "reaction-to-fire",
        "LinCrete GFRC with acoustic tissue and mineral wool backing",
        "reported_test_class_in_epd",
    );
    let loc = place(3, "Extraordinary Effects, Fire");
    for anchor in [
        "acoustic tissue and mineral wool backing",
        "EN 13501-1",
        "A2 for building material class, s1 for",
        "d0 for burning droplets",
    ] {
        confirm(&text, anchor)?;
    }
    facts.put(
        "reaction_to_fire",
        json!({"class":"A2-s1,d0","classification_standard":"EN 13501-1"}),
        None,
        &loc,
        &c,
    );
    facts.put("performance_documents",json!({"document_type":"EPD reporting a fire classification","declaration_id":"EPD-LIN-20250235-CBA1-EN","classification_standard":"EN 13501-1","property":"reaction_to_fire"}),None,&loc,&c);

    let loc = place(3, "Constructional data, Coefficient of thermal expansion");
    let c = conditions(
        "thermal-expansion",
        "LinCrete GFRC",
        "technical_performance_in_epd",
    );
    let low = amount(&text, r"coefficientofthermalexpansion([0-9]+)-")?;
    let high = amount(&text, r"coefficientofthermalexpansion[0-9]+-([0-9]+)10k")?;
    facts.put(
        "thermal_expansion_coefficient",
        json!({"minimum":low,"maximum":high}),
        Some("10⁻⁶/K"),
        &loc,
        &c,
    );

    let text = pdf_text(doc, 6)?;
    confirm(
        &text,
        "deconstructed or demolished and transported directly to landfill",
    )?;
    let mut c = conditions("dismantling", "LinCrete facade panels", SCENARIO);
    c["module"] = json!("C1");
    facts.put(
        "disassembly",
        json!({"scenario":"deconstruction or demolition"}),
        None,
        &place(6, "End of life, C1"),
        &c,
    );
    let km = amount(&text, r"theassumedtransportdistanceof([0-9]+)km")?;
    let mut c = conditions("transport-to-landfill", "LinCrete facade panels", SCENARIO);
    c["module"] = json!("C2");
    facts.put(
        "transport_scenario",
        json!({"destination":"landfill","distance":km}),
        Some("km"),
        &place(6, "End of life, C2"),
        &c,
    );
    let share = amount(&text, r"landfillingof([0-9]+)%oflincretepanels")?;
    let mut c = conditions("landfilling", "LinCrete facade panels", SCENARIO);
    c["module"] = json!("C4");
    facts.put(
        "recovery_route",
        json!({"route":"landfill","share":share}),
        Some("%"),
        &place(6, "End of life, C4"),
        &c,
    );
    Ok(())
}
