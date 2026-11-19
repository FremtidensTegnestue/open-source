---
type: reference
title: "AEFOROS / BIM + LCA"
description: "Materialekontrol, match til LCI-data, beregning og resultatvisning i Revit."
tags: ["vandkunsten", "aeforos", "tool"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-ab81016471dd893f68a527ce
    resource: repo://extracted/opensource.vandkunsten.com/05_aeforos/index.txt
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# AEFOROS / BIM + LCA

Materialekontrol, match til LCI-data, beregning og resultatvisning i Revit.

Originalside: [AEFOROS / BIM + LCA](https://opensource.vandkunsten.com/05_aeforos/). Platform: **Dynamo / Python / Revit / Excel**.

## Originalfiler hos udgiveren

| Fil | Størrelse |
| --- | ---: |
| [161107_VK_LCA.pdf](https://opensource.vandkunsten.com/05_aeforos/161107_VK_LCA.pdf) | 11,292,111 byte |
| [Aeforos_Vandkunsten.zip](https://opensource.vandkunsten.com/05_aeforos/Aeforos_Vandkunsten.zip) | 2,330,689 byte |
| [VK_aeforos_500x500.jpg](https://opensource.vandkunsten.com/05_aeforos/VK_aeforos_500x500.jpg) | 334,422 byte |
| [VK_oekobaudat_import_2015.zip](https://opensource.vandkunsten.com/05_aeforos/VK_oekobaudat_import_2015.zip) | 1,269,259 byte |

## Dataflow og pakker

Projektsiden beskriver to trin: kontrol af materialer og ID-match i Revit, efterfulgt af LCA-beregning og farvelagt resultatvisning. Resultater kan desuden eksporteres til Excel.

Den udpakkede AEFOROS-pakke indeholder `Aeforos.dyn`, `Aeforos_PreCheck.dyn`, `Aeforos_Combined.dyn`, `oekobaudat_concept_v6.xlsm` og `Results.xlsx`, samt hjælpeværktøjer til materialer, navngivning og klassifikation. Det separate ÖKOBAUDAT-importværktøj ligger i en anden ZIP. Stierne fremgår af ZIP-manifest og workbook-register.

Dynamo-filerne er katalogiseret, og tilgængelige scriptfragmenter fra definitionerne er udtrukket til `extracted/dynamo/`. Dette er en statisk udtrækning, ikke en komplet oversættelse af Dynamo-grafernes adfærd.

## Dataversion og dokumentation

Siden kalder den medfølgende database en concept-database baseret på ÖKOBAUDAT 2015. Databasen er ikke opdateret her. Præsentationen `161107_VK_LCA.pdf` er hentet med søgbar tekst. Konferenceartiklens direkte link fejler; alternative DTU-forsøg er registreret i dækningsstatus.

## Muligt genbrug

Adskil materialeregistrering, ID-mapping, enhedskontrol og beregningskerne. Bevar oplysninger om manglende materialer som strukturerede resultater, så en agent kan bede om afklaring før en beregning.

## Kontrolstatus og rettigheder

Medleveret concept-database er baseret på ÖKOBAUDAT 2015.

MIT som udgangspunkt på site; databaser og øvrige komponenter undersøges separat. Ingen upstream-programmer eller makroer er afviklet.

[Projektregister](../../catalog/projects.json) · [Filregister](../../catalog/files.json) · [Workbook-register](../../catalog/workbooks.json) · [ZIP-manifest](../../catalog/archives.json) · [PDF-register](../../catalog/pdfs.json)

I den offentlige Git-pakke peger links til originalfiler og regnearksfaner på udgiverens filer. Det fulde lokale arkiv og JSON-celleudtræk kan genskabes; se [arkivguiden](../../docs/ARKIV.md).
