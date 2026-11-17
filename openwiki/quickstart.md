---
type: reference
title: "Start her — åbne materialedata og modelberegninger"
description: "Find projektmateriale, materialedata, det afprøvede samlede CAD/BIM-forløb og dokumentation til videre genbrug."
tags: ["programs", "cad", "agents"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-16ad9c57da182f87c66c86c2
    resource: repo://catalog/coverage.json
  - id: openwiki-source-017c3c3643ad29273d907498
    resource: repo://catalog/projects.json
  - id: openwiki-source-73b4555f357268d358b789e1
    resource: repo://data/parquet/manifest.json
  - id: openwiki-source-a6d1c9d73c2af4ed4fe919be
    resource: repo://data/README.md
  - id: openwiki-source-d4ea6da975039059cb886f5a
    resource: repo://scripts/build_database.py
  - id: openwiki-source-af5ac3680872a1b8fc55ee8d
    resource: repo://sources/programmer/installation.json
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# Start her — åbne materialedata og modelberegninger

Dette repository samler Vandkunstens offentlige værktøjer og projektmateriale som et lokalt kildearkiv. Sektionen [Programmer](programmer/index.md) dokumenterer desuden serverens Solidcraft- og BIMcraft-installationer. Indholdet er katalogiseret; originalprogrammerne er ikke funktionstestet.

## Ny bruger: begynd her

[README](../README.md) forklarer projektet på almindeligt dansk. [Begynderguiden](../docs/KOM-GODT-I-GANG.md) viser både læsning uden installation, brug med agent og egne kommandoer. [Ordlisten](../docs/ORDLISTE.md) forklarer fag- og værktøjsbegreber.

Hele materialedatasættet følger med som Parquet i `data/parquet/`. Gendan den lokale SQLite-database med `python scripts/build_database.py`, når Python-pakkerne er installeret. Se [dataguiden](../data/README.md). Rå kildearkiver er en særskilt samling og kan hentes efter behov.

## Find den relevante indgang

| Opgave | Wiki |
| --- | --- |
| Afprøvet samlet CAD → BIM → materialeberegning | [Overførsel, modelændring og returkontrol](../examples/integrated-workflow/README.md) |
| Beregn fra Solidcraft- og BIMcraft-modeller | [Modelberegninger og agent-skill](workflows/modelberegninger.md) |
| Søg i den leverede materialedatabase | [Database, kilder og CLI](data/materialedatabase.md) |
| Fælles vision: brede materialedata, beregninger, CLI og agent-skills | [Åben materialeplatform](ideer/aaben-materialeplatform.md) |
| Produktidéer og prioritering for danske arkitekter | [Idékatalog](ideer/danske-arkitektvaerktoejer.md) |
| Parametrisk CAD, detaljer og 3D-print | [Solidcraft](programmer/solidcraft.md) |
| Bygningsmodeller, tegninger og IFC | [BIMcraft](programmer/bimcraft.md) |
| Hurtig LCA fra få oplysninger | [LCA estimator](tools/lca-estimator.md) og [EarlyBird](tools/earlybird-lca.md) |
| Træbrædders dimensionsændring | [Træfacader](tools/trae-udvidelse.md) |
| Dagslys, DLA og UDI | [Dagslys](tools/dagslys.md) |
| Mængder fra BIM til LCA | [AEFOROS](tools/aeforos.md) |
| Mængder fra BIM til totaløkonomi | [LCC + Revit](tools/lcc-revit.md) |
| Lisbjerg: beregnede mængder, rapport og manglende oplysninger | [Lisbjerg Bakke](tools/lisbjerg-bakke.md) |
| Hjemmesidens PHP/HTML-kildekode | [Lille Arne](tools/lille-arne.md) |
| Hvad er hentet, og hvad mangler? | [Arkiv og proveniens](archive/proveniens.md) |
| Hvordan søges og gendannes udtræk? | [Arbejdsgange](archive/arbejdsgange.md) |
| Hvilke licenser er fundet? | [Rettigheder](archive/rettigheder.md) |
| Hvordan kan materialet blive agentklart? | [Videreudvikling](concepts/agent-og-rust.md) |

## Brug materialet

Start med projektets side og følg links til originalfil og søgbart udtræk. Brug `catalog/projects.json` som maskinlæsbart projektregister og `catalog/files.json` til stier, filstørrelser og SHA-256. `catalog/workbooks.json` finder Excel-ark, herunder skjulte faner; `catalog/pdfs.json` finder PDF-tekst med sidemarkeringer.

Søg fra repository-roden med `rg -n "fugemål|matchscore|LCI" openwiki extracted`. Et fund i et tekstudtræk skal ved præcis faglig anvendelse kontrolleres mod originalfilen.

## Materialedatabasen

Den første database og et JSON-CLI er nu leveret med fire indsamlinger, originale kildefiler og dokumenterede observationer. Se [databaseguiden](data/materialedatabase.md) for indhold, søgning, reproduktion og kontroller. Der er nu også leveret [modeladaptere, beregninger og en agent-skill](workflows/modelberegninger.md) med dokumenterede kontrolcases. Materiale- og datavalg er eksplicitte, og uafklarede forhold vises som delvise resultater.

## Status for Vandkunsten-arkivet

Forsiden, otte projektsider og øvrige fundne interne ressourcer er arkiveret. GitHub-snapshottet har en registreret commit og et separat Git-bundle. En ekstern konferenceartikel kunne ikke downloades; SBi 2020:04 blev reddet via AAU. Se [dækningsstatus](../catalog/coverage.json).

Rust-omskrivning, MCP-server, makroafvikling og validering i originalprogrammer er fremtidigt arbejde. Dette arkiv har ingen fælles ny licens for alt indhold.

## Første projektanalyse

[Lisbjerg Bakke-rapporten](../reports/lisbjerg-bakke/README.md) afprøver arbejdsgangen på de originale ARK-/KON-modeller og 132 tegningssider. Den skelner mellem kildeoplysninger, programberegnede mængder og eksplicitte referencescenarier. De to fagmodeller lægges ikke sammen; manglende data og værktøjsbegrænsninger er registreret med prioritet og ansvar.

## Afprøvet samlet forløb

[Solidcraft → BIMcraft → materialeværktøj](../examples/integrated-workflow/README.md) er gennemført på en lille, veldokumenteret model med tre dele og en modelændring. Geometrien overføres gennem GLB og måles fra BIMcrafts egne familietrekanter. Materialereferencer er eksplicitte, og både beregninger, returimport og afvisning af gamle bindinger er efterprøvet. Det er et generisk komponentforløb med nyt BIM-projekt pr. revision.
