---
type: reference
title: "Udvidelsesberegner for træfacader"
description: "Beregner fugemål og dækmål ud fra montagedato, brætbredde og trægruppe."
tags: ["vandkunsten", "trae-udvidelse", "tool"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:09:45.141Z
sources:
  - id: openwiki-source-63d5efcf14976e1fb49dbbbe
    resource: repo://extracted/opensource.vandkunsten.com/04_udvidelse-trae/index.txt
  - id: openwiki-source-646ed3c1fa5f05e64e2d7c09
    resource: repo://extracted/workbooks/archive/opensource.vandkunsten.com/04_udvidelse-trae/VK_udvidelse-tr%C3%A6.xlsx/01-beregner.csv
generated: { by: "codex", at: "2026-11-17T23:09:45.141Z" }
---

# Udvidelsesberegner for træfacader

Beregner fugemål og dækmål ud fra montagedato, brætbredde og trægruppe.

Originalside: [Udvidelsesberegner for træfacader](https://opensource.vandkunsten.com/04_udvidelse-trae/). Platform: **Excel**.

## Originalfiler hos udgiveren

| Fil | Størrelse |
| --- | ---: |
| [VK_udvidelse-trae_500x500.jpg](https://opensource.vandkunsten.com/04_udvidelse-trae/VK_udvidelse-trae_500x500.jpg) | 117,122 byte |
| [VK_udvidelse-træ.xlsx](https://opensource.vandkunsten.com/04_udvidelse-trae/VK_udvidelse-tr%C3%A6.xlsx) | 203,310 byte |

## Beregningens opbygning

Fanen `beregner` indeholder montagedato, målt brætbredde og to grupper af træarter. Datoen omsættes til måned, som knyttes til tabeller for temperatur, relativ luftfugtighed og omtrentlig ligevægtsfugtighed. Resultaterne er fugemål og nyt dækmål i to retninger.

Der er 15 formelceller i beregnerfanen og en separat licensfane. Trægrupperne er fyr/gran/eg og bøg/birk. Dimensionskoefficienterne tilskrives i arket Larsen og Riberholt (2005).

## Opmærksomhed ved genbrug

Celle K24 indeholder `=K17*D5/1000*7`, mens J24 og cellerne i den næste trægruppe anvender E36. Det hårdkodede syvtal skal fagligt afklares, før formlen ændres eller oversættes. Fundet dokumenterer en forskel i formler; det beviser ikke i sig selv en fejl.

En første agentfunktion kunne vise input, valgt måned, fugtforudsætninger og begge resultater. Fysisk anvendelighed og tolerancer er ikke efterprøvet her.

## Kontrolstatus og rettigheder

Månedsbaseret klimamodel; formlernes anvendelighed er ikke fysisk efterprøvet.

MIT i licensark. Ingen upstream-programmer eller makroer er afviklet.

[Projektregister](../../catalog/projects.json) · [Filregister](../../catalog/files.json) · [Workbook-register](../../catalog/workbooks.json) · [ZIP-manifest](../../catalog/archives.json) · [PDF-register](../../catalog/pdfs.json)

## Inspicerede Excel-faner

- [beregner](https://opensource.vandkunsten.com/04_udvidelse-trae/VK_udvidelse-tr%C3%A6.xlsx): visible, 15 formelceller.
- [license](https://opensource.vandkunsten.com/04_udvidelse-trae/VK_udvidelse-tr%C3%A6.xlsx): visible, 0 formelceller.

I den offentlige Git-pakke peger links til originalfiler og regnearksfaner på udgiverens filer. Det fulde lokale arkiv og JSON-celleudtræk kan genskabes; se [arkivguiden](../../docs/ARKIV.md).
