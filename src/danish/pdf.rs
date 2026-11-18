//! Decode text from original PDFs and retain glyph positions in PDF points.
use anyhow::{Context, Result, ensure};
use pdf_extract::{Document, MediaBox, OutputDev, OutputError, Transform};
use serde::Deserialize;
use serde_json::Value;
use std::{collections::BTreeMap, path::Path};

#[derive(Deserialize)]
pub(super) struct RowRecipe {
    pub page: u32,
    pub line: usize,
    pub header: usize,
    pub indicator: String,
    pub unit: String,
    pub modules: Vec<String>,
    bounds: Vec<[f64; 4]>,
    sha256: String,
    glyph_counts: Vec<usize>,
}
#[derive(Deserialize)]
pub(super) struct Recipe {
    pub material: Value,
    pub reference_locator: String,
    pub original_reference: String,
    pub detail: String,
    pub tables: Vec<RowRecipe>,
}

#[derive(Default)]
pub(super) struct GlyphPage {
    glyphs: Vec<(f64, f64, f64, String)>,
    top: f64,
}
impl OutputDev for GlyphPage {
    fn begin_page(
        &mut self,
        _: u32,
        media: &MediaBox,
        _: Option<(f64, f64, f64, f64)>,
    ) -> Result<(), OutputError> {
        self.top = media.ury;
        Ok(())
    }
    fn end_page(&mut self) -> Result<(), OutputError> {
        Ok(())
    }
    fn begin_word(&mut self) -> Result<(), OutputError> {
        Ok(())
    }
    fn end_word(&mut self) -> Result<(), OutputError> {
        Ok(())
    }
    fn end_line(&mut self) -> Result<(), OutputError> {
        Ok(())
    }
    fn output_character(
        &mut self,
        trm: &Transform,
        width: f64,
        _: f64,
        font_size: f64,
        c: &str,
    ) -> Result<(), OutputError> {
        self.glyphs.push((
            trm.m31,
            self.top - trm.m32,
            width * (font_size * trm.m11).abs(),
            c.to_owned(),
        ));
        Ok(())
    }
}
pub(super) fn document(path: &Path) -> Result<Document> {
    let mut doc = Document::load(path)?;
    if doc.is_encrypted() {
        doc.decrypt("")?;
    }
    Ok(doc)
}
pub(super) fn extract_page(doc: &Document, page: u32) -> Result<GlyphPage> {
    let mut glyphs = GlyphPage::default();
    pdf_extract::output_doc_page(doc, &mut glyphs, page)?;
    Ok(glyphs)
}
fn normalized(text: &str) -> String {
    text.replace(['−', '–', '‑'], "-")
}

impl GlyphPage {
    fn cell(&self, [left, top, right, bottom]: [f64; 4]) -> String {
        let mut parts: Vec<_> = self
            .glyphs
            .iter()
            .filter(|(x, y, _, c)| {
                *x >= left - 0.25
                    && *x < right + 0.15
                    && *y >= top - 0.45
                    && *y <= bottom + 0.5
                    && !c.trim().is_empty()
            })
            .collect();
        parts.sort_by(|a, b| a.0.total_cmp(&b.0));
        normalized(&parts.iter().map(|p| p.3.as_str()).collect::<String>())
    }
    /// Group horizontal text baselines, reconstructing only the whitespace needed to
    /// distinguish cells. Other PDF templates remain archived for later review.
    pub(super) fn lines(&self) -> Vec<String> {
        // PDFs often typeset the exponent in m² or m³ as a separate raised digit.
        // Rejoin only a digit immediately adjacent to the end of a metre glyph.
        let mut glyphs = self.glyphs.clone();
        for index in 1..glyphs.len() {
            if !matches!(glyphs[index].3.as_str(), "2" | "3") {
                continue;
            }
            let (previous, current) = glyphs.split_at_mut(index);
            let digit = &mut current[0];

            if let Some(metre) = previous.iter().rev().take(3).find(|g| {
                matches!(g.3.as_str(), "m" | "M")
                    && (g.0 + g.2 - digit.0).abs() < 1.6
                    && (1.0..=6.0).contains(&(g.1 - digit.1))
            }) {
                digit.1 = metre.1;
                digit.3 = if digit.3 == "2" {
                    "²".into()
                } else {
                    "³".into()
                };
            }
        }
        let mut sorted: Vec<_> = glyphs.iter().filter(|g| !g.3.trim().is_empty()).collect();
        sorted.sort_by(|a, b| a.1.total_cmp(&b.1));
        let mut lines = Vec::new();
        let mut i = 0;
        while i < sorted.len() {
            let base = sorted[i].1;
            let mut j = i + 1;
            while j < sorted.len() && sorted[j].1 - base < 1.0 {
                j += 1;
            }
            let mut group = sorted[i..j].to_vec();
            group.sort_by(|a, b| a.0.total_cmp(&b.0));
            let mut text = String::new();
            let mut end = f64::NEG_INFINITY;
            for (x, _, w, c) in group {
                if !text.is_empty() && *x - end > 1.25 {
                    text.push(' ');
                }
                text.push_str(c);
                end = *x + *w;
            }
            lines.push(normalized(&text));
            i = j;
        }
        lines
    }
}
pub(super) fn read_locked(path: &Path, recipe: &Recipe) -> Result<Vec<Vec<String>>> {
    let doc = document(path)?;
    let mut pages = BTreeMap::new();
    let mut all = Vec::new();
    for row in &recipe.tables {
        if let std::collections::btree_map::Entry::Vacant(slot) = pages.entry(row.page) {
            slot.insert(extract_page(&doc, row.page)?);
        }
        let page = pages.get(&row.page).context("missing extracted page")?;
        let mut cells: Vec<_> = row.bounds.iter().map(|b| page.cell(*b)).collect();
        if super::sha(cells.join("\n").as_bytes()) != row.sha256 {
            // Some embedded fonts report fallback widths. Glyph stream order and
            // the first character's anchored position still identify each cell.
            let anchored: Option<Vec<String>> = row
                .bounds
                .iter()
                .zip(&row.glyph_counts)
                .map(|([left, top, _, bottom], length)| {
                    let start = page
                        .glyphs
                        .iter()
                        .enumerate()
                        .filter(|(_, (x, y, _, text))| {
                            (*x - *left).abs() < 0.8
                                && *y >= *top - 0.5
                                && *y <= *bottom + 0.5
                                && !text.trim().is_empty()
                        })
                        .min_by(|(_, a), (_, b)| {
                            ((a.0 - *left).abs()).total_cmp(&(b.0 - *left).abs())
                        })?
                        .0;
                    Some(normalized(
                        &page
                            .glyphs
                            .get(start..start + *length)?
                            .iter()
                            .map(|g| g.3.as_str())
                            .collect::<String>(),
                    ))
                })
                .collect();
            if let Some(values) = anchored {
                cells = values
            }
        }
        ensure!(
            super::sha(cells.join("\n").as_bytes()) == row.sha256,
            "Native PDF result failed its independent text checksum in {} page {} line {} ({})",
            path.display(),
            row.page,
            row.line,
            row.indicator
        );
        all.push(cells);
    }
    Ok(all)
}
