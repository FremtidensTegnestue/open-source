//! Recognize a conservative subset of new publisher PDF templates, using native glyph baselines.
use super::*;
use std::collections::BTreeSet;

fn unit_key(u: &str) -> String {
    u.to_lowercase()
        .replace("₂", "2")
        .replace("³", "3")
        .chars()
        .filter(|c| !c.is_whitespace() && !matches!(c, '[' | ']' | '-' | '.'))
        .collect()
}
fn field(cover: &str, label: &str) -> Result<Value> {
    let re = Regex::new(&format!(r"(?mi)^\s*(?:{label}):[ \t]*(\S+)[ \t]*$"))?;
    Ok(re
        .captures(cover)
        .map(|c| Value::String(c[1].to_owned()))
        .unwrap_or(Value::Null))
}
pub(super) fn extract(e: &Entry, path: &Path, basis: &str) -> Result<Product> {
    let doc = match pdf::document(path) {
        Ok(d) => d,
        Err(_) => return Ok(Product::excluded("unreadable_PDF")),
    };
    let mut pages = Vec::new();
    for pg in doc.get_pages().into_keys() {
        match pdf::extract_page(&doc, pg) {
            Ok(p) => pages.push(p.lines()),
            Err(_) => return Ok(Product::excluded("unsupported_PDF_text")),
        }
    }
    read_lines(e, basis, &pages)
}
fn read_lines(e: &Entry, basis: &str, pages: &[Vec<String>]) -> Result<Product> {
    let (amount, u) = reference(basis).context("Unexpected EPD basis")?;
    if u == "m" {
        return Ok(Product::excluded("linear_unit_requires_review"));
    }
    let caption = Regex::new(
        r"(?i)(?:environmental impacts?|miljøpåvirkninger|results?)\s+(?:per|pr\.?)\s+\[?\s*(?:(\d+(?:[.,]\d+)?)\s*)?(m[23²³]?|kg|stk\.?|piece|pcs\.?|t)(?:\s|$|\])",
    )?;
    let declared = Regex::new(
        r"(?i)^(?:declared unit|deklareret enhed)\s+(\d+(?:[.,]\d+)?)\s+(m[23²³]?|kg|stk\.?|piece|pcs\.?|t)(?:\s|$)",
    )?;
    let head = Regex::new(r"(?i)^(?:parameter\s+(?:unit|enhed)|indicator(?:\s+unit)?)\s+(.*)$")?;
    let module = Regex::new(r"^(?:[ABC][1-7](?:-(?:[ABC])?[1-7])?|D)$")?;
    let short_range = Regex::new(r"^([ABC])(\d)-(\d)$")?;
    let total_row = Regex::new(r"(?i)^gwp-total(?:\s|\[)")?;
    let number = Regex::new(r"^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:[Ee][+-]?\d+)?$")?;
    let mut rows = Vec::new();
    let mut refs = Vec::new();
    let mut markers = 0;
    for (page_no, lines) in pages.iter().enumerate() {
        let mut header = 0;
        let mut columns = Vec::new();
        for (idx, line) in lines.iter().enumerate() {
            if let Some(c) = declared.captures(line) {
                refs.push((
                    reference(&format!("{} {}", &c[1], &c[2])),
                    format!("PDF page {} native text line {}", page_no + 1, idx + 1),
                ));
            }
            if let Some(c) = head.captures(line) {
                header = idx + 1;
                columns = c[1]
                    .split_whitespace()
                    .map(|x| short_range.replace(x, "${1}${2}-${1}${3}").to_string())
                    .collect();
                if !columns.iter().all(|x| module.is_match(x))
                    || columns.iter().collect::<BTreeSet<_>>().len() != columns.len()
                {
                    columns.clear();
                }
                continue;
            }
            if total_row.is_match(line) && !line.to_ascii_lowercase().starts_with("gwp-total =") {
                markers += 1;
            }
            if columns.is_empty() {
                continue;
            }
            let fields: Vec<_> = line.split_whitespace().collect();
            if fields.len() < columns.len() + 2 {
                continue;
            }
            let indicator = fields[0].to_ascii_lowercase();
            let (_, unit) = result_property(&indicator);
            if unit.is_empty() {
                continue;
            }
            let split = fields.len() - columns.len();
            let source_unit = fields[1..split].join(" ");
            if unit_key(&source_unit) != unit_key(unit) {
                continue;
            }
            if !fields[split..]
                .iter()
                .all(|s| number.is_match(s) || matches!(*s, "ND" | "MND" | "MNR" | "NPD" | "INA"))
            {
                continue;
            }
            if indicator == "gwp-total" {
                let title = lines[header.saturating_sub(6)..header - 1].join(" ");
                if let Some(c) = caption.captures(&title) {
                    let amount = c.get(1).map(|x| x.as_str()).unwrap_or("1");
                    refs.push((
                        reference(&format!("{amount} {}", &c[2])),
                        format!(
                            "PDF page {} table title above native header line {header}",
                            page_no + 1
                        ),
                    ));
                }
            }
            rows.push(ResultRow {
                page: (page_no + 1) as u32,
                line: idx + 1,
                header,
                indicator,
                unit: source_unit,
                modules: columns.clone(),
                cells: fields[split..].iter().map(|v| (*v).to_owned()).collect(),
            });
        }
    }
    if refs.is_empty()
        || refs
            .iter()
            .any(|(r, _)| r.as_ref() != Some(&(amount, u.clone())))
    {
        return Ok(Product::excluded("PDF_declared_amount_unconfirmed"));
    }
    if markers != 1 {
        return Ok(Product::excluded("multiple_or_missing_GWP_result_tables"));
    }
    if rows.iter().filter(|r| r.indicator == "gwp-total").count() != 1 {
        return Ok(Product::excluded("ambiguous_module_columns_or_GWP_unit"));
    }
    let mut repeat = BTreeMap::new();
    for row in &rows {
        *repeat.entry(result_property(&row.indicator).0).or_insert(0) += 1;
    }
    rows.retain(|r| repeat[&result_property(&r.indicator).0] == 1);
    let cover = pages.first().map(|p| p.join("\n")).unwrap_or_default();
    let declaration = json!({"issued":field(&cover,"Issued|Udstedt")?,"revision":field(&cover,"Revision")?,"valid_until":field(&cover,"Valid to|Gyldig til")?,"declaration_number":field(&cover,"No\\.|Nr\\.")?});
    let id = format!(
        "epd-danmark:record:{}",
        &sha(Url::parse(&e.detail)?.path().as_bytes())[..32]
    );
    let material = json!({"id":id,"name":e.name,"kind":"product","category":"declared_product_or_product_group","aliases":declaration["declaration_number"].as_str().into_iter().collect::<Vec<_>>(),
        "source_id":sid(&e.pdfs[0]),"source_locator":format!("Declaration cover and declared unit in {}",refs[0].1),
        "declaration":declaration,"detail_source_id":sid(&e.detail),"identity_scope":"publisher declaration listing; product(s) covered by the EPD","declared_unit":format!("{amount} {u}")});
    result(material, basis, &refs[0].1, rows, "native text")
}
#[cfg(test)]
mod tests {
    use super::*;
    fn sample() -> (Entry, Vec<Vec<String>>) {
        (
            Entry {
                name: "Test".into(),
                detail: format!("{INDEX}fixture/"),
                pdfs: vec![format!("{INDEX}test.pdf")],
            },
            vec![
                vec![
                    "No.: MD-fixture",
                    "Valid to: 2028-12-31",
                    "Declared unit 1 m2",
                    "ENVIRONMENTAL IMPACTS PER 1 M2",
                    "Parameter Unit A1-A3 A4 D",
                    "GWP-total [kg CO2 eq.] 3,12E-01 ND -7.6",
                ]
                .into_iter()
                .map(str::to_owned)
                .collect(),
            ],
        )
    }
    #[test]
    fn native_rows_preserve_modules_and_absence() {
        let (e, p) = sample();
        let got = read_lines(&e, "1 m²", &p).unwrap();
        assert_eq!(got.obs.len(), 3);
        assert_eq!(got.obs[0]["value"], 0.312);
        assert_eq!(got.obs[2]["module"], "D");
        assert!(got.obs[1]["value"].is_null());
    }
    #[test]
    fn incorrect_basis_disables_calculation() {
        let (e, p) = sample();
        assert!(read_lines(&e, "1000 kg", &p).unwrap().obs.is_empty());
    }
    #[test]
    fn repeated_scenarios_do_not_produce_a_unique_choice() {
        let (e, mut p) = sample();
        p[0][4] = "Parameter Unit A1-A3 D D".into();
        assert!(read_lines(&e, "1 m2", &p).unwrap().obs.is_empty());
    }
}

#[cfg(test)]
mod native_document_tests {
    use super::*;
    #[test]
    fn native_pdf_dictionary_and_page_geometry() {
        use pdf_extract::{Document, Object, Stream, dictionary};
        // Typeset an independently constructed PDF with real text operators.
        let mut doc = Document::with_version("1.5");
        let pages_id = doc.new_object_id();
        let font =
            doc.add_object(dictionary! {"Type"=>"Font","Subtype"=>"Type1","BaseFont"=>"Helvetica"});
        let resources = doc.add_object(dictionary! {"Font"=>dictionary!{"F1"=>font}});
        let contents=doc.add_object(Stream::new(dictionary!{}, b"BT /F1 10 Tf 40 720 Td 15 TL (Declared unit 1 m2) Tj T* (ENVIRONMENTAL IMPACTS PER 1 M2) Tj T* (Parameter Unit A1-A3 D) Tj T* (GWP-total [kg CO2 eq.] 3.21E+01 -4.56E-02) Tj ET".to_vec()));
        let page=doc.add_object(dictionary!{"Type"=>"Page","Parent"=>pages_id,"Resources"=>resources,"Contents"=>contents});
        doc.objects.insert(pages_id,Object::Dictionary(dictionary!{"Type"=>"Pages","Kids"=>vec![page.into()],"Count"=>1,"MediaBox"=>vec![0.into(),0.into(),612.into(),792.into()]}));
        let catalog = doc.add_object(dictionary! {"Type"=>"Catalog","Pages"=>pages_id});
        doc.trailer.set("Root", catalog);
        let mut tmp = tempfile::NamedTempFile::new().unwrap();
        doc.save_to(tmp.as_file_mut()).unwrap();
        let e = Entry {
            name: "Example".into(),
            detail: format!("{INDEX}example/"),
            pdfs: vec![format!("{INDEX}example.pdf")],
        };
        let result = extract(&e, tmp.path(), "1 m2").unwrap();
        assert_eq!(result.status, "imported");
        assert_eq!(result.obs.len(), 2);
        assert_eq!(result.obs[0]["value"], 32.1);
        assert_eq!(result.obs[1]["value"], -0.0456);
    }
}

// This integration check runs only where the separately acquired EPD originals are installed.
#[cfg(test)]
mod publisher_tests {
    use super::*;
    #[test]
    #[ignore = "requires local EPD Danmark source archive"]
    fn fresh_template_on_original_published_declaration() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"));
        let lock: Value =
            serde_json::from_slice(&fs::read(root.join(PUBLIC).join("sources.lock.json")).unwrap())
                .unwrap();
        let url = "https://www.epddanmark.dk/media/3ctltuob/md-23055-en_rev1.pdf";
        let sha = lock["originals"][url]["sha256"].as_str().unwrap();
        let entry = Entry {
            name: "Tystø".into(),
            detail: format!("{INDEX}a-gain-aps/tysto/?alttemplate=EPDpopup&lang=da-dk"),
            pdfs: vec![url.into()],
        };
        let r = extract(&entry, &root.join(RAW).join(format!("{sha}.pdf")), "1 m2").unwrap();
        assert_eq!(r.status, "imported");
        let gwp = r
            .obs
            .iter()
            .find(|v| v["property"] == "gwp_total" && v["module"] == "A1-A3")
            .unwrap();
        assert_eq!(gwp["value"], -0.768);
    }
}
