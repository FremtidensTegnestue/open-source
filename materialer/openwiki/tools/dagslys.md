---
type: reference
title: "Dagslyssimulering DLA / UDI"
description: "Dagslysanalyse fra tegninger og modeller med tilhørende plugins, eksempel og vejrfiler."
tags: ["vandkunsten", "dagslys", "tool"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-edc8c81c0695272a9cca0926
    resource: repo://extracted/opensource.vandkunsten.com/02_DLA-UDI/index.txt
  - id: openwiki-source-caa6ccca9255ba4b6f189aaa
    resource: repo://upstream/Daylight_VK-01/License.txt
  - id: openwiki-source-08d7e944db6e2ab76468554d
    resource: repo://upstream/Daylight_VK-01/README.md
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# Dagslyssimulering DLA / UDI

Dagslysanalyse fra tegninger og modeller med tilhørende plugins, eksempel og vejrfiler.

Originalside: [Dagslyssimulering DLA / UDI](https://opensource.vandkunsten.com/02_DLA-UDI/). Platform: **Rhino / Grasshopper / Radiance**.

## Originalfiler hos udgiveren

| Fil | Størrelse |
| --- | ---: |
| [VK_dagslys_500x500px.jpg](https://opensource.vandkunsten.com/02_DLA-UDI/VK_dagslys_500x500px.jpg) | 110,372 byte |

## Indhold og afhængigheder

Den linkede GitHub-kilde er arkiveret i `upstream/Daylight_VK-01/`; commit-identiteten findes i `catalog/upstream.json`. Hele den tilgængelige Git-historik er bevaret i `archive/Daylight_VK-01.bundle`.

Repositoryets README angiver Rhino 6 eller 7, Grasshopper, Ladybug Tools 1.1.0, Honeybee+ 0.0.06 og Radiance. Derudover nævnes Pufferfish, Bifocals, Elefront, HumanUI, Human/Tree Frog, LunchBox, Metahopper og TT Toolbox. Det er kildens historiske afhængighedsbeskrivelse, ikke en nutidig kompatibilitetsgaranti.

Her findes scriptet `03. VK_DaylightMetrics_script.gh`, en `.3dm`-eksempelmodel, PDF-tutorial og pakker med add-ins og vejrfiler. De medfølgende ZIP-filer og indlejrede ZIP-filer er katalogiseret og pakket ud. Der er ikke hentet alle nye versioner fra tredjepartswebsites.

## Særlig licensobservation

`License.txt` indeholder GNU GPL version 3. Derfor må hjemmesidens generelle MIT-angivelse ikke bruges som eneste licensoplysning for denne pakke. Medfølgende plugins har egne licensfiler og rettighedsforhold.

## Muligt genbrug

Undersøg først, hvordan Grasshopper-scriptet klargør geometri og kalder simuleringen. En agentgrænseflade kan senere koordinere input og resultater. En fuld ny dagslysmotor er ikke implementeret eller nødvendiggjort af denne arkivering.

## Kontrolstatus og rettigheder

Binære Grasshopper-filer; kræver eksisterende software og flere plugins.

GPL v3-tekst i upstream/Daylight_VK-01/License.txt; tredjepartsplugins har egne vilkår. Ingen upstream-programmer eller makroer er afviklet.

[Projektregister](../../catalog/projects.json) · [Filregister](../../catalog/files.json) · [Workbook-register](../../catalog/workbooks.json) · [ZIP-manifest](../../catalog/archives.json) · [PDF-register](../../catalog/pdfs.json)

I den offentlige Git-pakke peger links til originalfiler og regnearksfaner på udgiverens filer. Det fulde lokale arkiv og JSON-celleudtræk kan genskabes; se [arkivguiden](../../docs/ARKIV.md).
