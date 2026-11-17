---
type: reference
title: "Materialedatabasen — data, kilder og CLI"
description: "Leveret SQLite-database med kildebevarede materialeobservationer, originalfiler, kilde-manifester og JSON-CLI."
tags: ["materials", "database", "sources", "cli", "provenance"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-5002e118bbd020c45088b784
    resource: repo://data/catalog.json
  - id: openwiki-source-73b4555f357268d358b789e1
    resource: repo://data/parquet/manifest.json
  - id: openwiki-source-a6d1c9d73c2af4ed4fe919be
    resource: repo://data/README.md
  - id: openwiki-source-08de71f590fd8ef2b9c6d5b1
    resource: repo://data/verification.json
  - id: openwiki-source-7d4e16f478ad8f8f35bc2e06
    resource: repo://docs/DATABASE.md
  - id: openwiki-source-d4ea6da975039059cb886f5a
    resource: repo://scripts/build_database.py
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# Materialedatabasen

Der er nu bygget en samlet lokal SQLite-database med kildebevarede materialedata og et JSON-CLI til søgning, opslag og kontrol. Første indsamling dækker bredt på tværs af materialer og egenskaber; den er ikke afgrænset til træ eller facadebeklædning.

## Faktisk leverance

| Datasæt | Kildebestemte poster | Numeriske observationer |
| --- | ---: | ---: |
| ÖKOBAUDAT, publicerede maskinlæsbare miljødata | 7.067 | 1.962.722 |
| OpenStudio og EnergyPlus, tekniske materiale-/simuleringsdata | 3.183 | 15.127 |
| USDA Wood Handbook, træets fugt, svind, mekanik og varme | 325 | 5.038 |
| Danske BR18-tabeller 7–11 | 586 | 2.695 |
| **I alt** | **11.161** | **1.985.582** |

Der er bevaret 7.135 registrerede kildefiler med SHA-256. Filer under `data/raw/` fylder cirka 706 MB inklusive tekstudtræk og hentemetadata. SQLite-filen fylder cirka 8,8 GB. `data/catalog.json` er den maskinlæsbare optælling for dette snapshot.

En post er en kildebestemt identitet, ikke nødvendigvis et unikt materiale. Produkter, generiske materialer, konstruktioner, energibærere og procesfaktorer indgår. En materialetype kan derfor have mange kilder, produkter, metoder og betingelser og tilsvarende mange observationer.

## Hvilke tal findes?

Miljødata omfatter modulopdelte indikatorer for klima og andre miljøpåvirkninger samt energi-, ressource- og affaldsdata, når kilden har dem. Metode og deklareret mængde bevares, og modul D er særskilt.

Tekniske data omfatter blandt andet densitet, varmeledningsevne, varmekapacitet, lagtykkelser, varmemodstand, glasoptik og fugtmodeller. Mange værdier stammer fra simuleringsbiblioteker; deres oprindelige type og betingelser er bevaret.

Trædata omfatter total svind fra grønt til ovntørt træ, særskilte koefficienter for fugtbetinget dimensionsændring, ligevægtsfugt samt styrke-, stivheds- og varmeegenskaber. Retning, fugttilstand, temperatur og prøvetype følger værdierne. Total svind i procent må ikke forveksles med ændring pr. procentpoint fugt.

De danske tabeller giver blandt andet klima- og massefaktorer, energi- og brændstoffaktorer samt transport- og affaldsbehandlingsværdier. Installationsfaktorer har særskilt areal-/årsgrundlag og er ikke produkt-EPD'er.

## Organisation og kilder

- [Databaseguide](../../docs/DATABASE.md): skema, CLI, reproduktion og fortolkning.
- [Dækningsrapport](../../docs/COVERAGE.md): faktiske antal og aktuelle mangler.
- [Samlet JSON-katalog](../../data/catalog.json): statistik og datasetrapporter.
- [Verifikationsrapport](../../data/verification.json): udførte kontroller og deres grænser.
- Kildedokumentation: [miljødata](../../docs/sources/environmental.md), [tekniske data](../../docs/sources/technical.md), [trædata](../../docs/sources/wood.md), [danske tabeller](../../docs/sources/br18.md).

Originaler ligger under `data/raw/<datasæt>/`. Udtræk og kilde-manifester ligger under `data/staging/<datasæt>/`; hver collector ligger i `collectors/`. Tabellen `sources` registrerer originalsti, URL, hentetid, checksum og rettigheder. Hver observation har materiale, egenskab, værdi, original tekst, enhed, kontekst og en præcis kildelokation som JSON Pointer, Excel-celle eller PDF-side/tabel/række.

Miljødataenes originaler er de publicerede udvidede JSON-filer. Der er registreret 4.685 bilagsadresser, men bilagene er ikke alle downloadet. Den danske indsamling har hentet alle 24 forskellige direkte PDF-links i tabel 7. Hele USDA Wood Handbook og de anvendte kapitler er arkiveret; kun de dokumenterede tabeller er struktureret.

## Brug databasen

Fra `/home/admin/Fremtidenstegnestue/open-source`:

```sh
python3 materials.py stats
python3 materials.py search beton --limit 5
python3 materials.py observations --property density --limit 10
python3 materials.py observations --material wood:alder-red --property shrinkage_radial
python3 materials.py observations --property moisture_dimensional_change_coefficient_tangential --limit 5
python3 materials.py sources --id wood:chapter-13
```

Svarene er JSON. Brug fundne post-ID'er til `show` og `observations`, og følg `source_id` videre til originalen. Søgningen er tekstsøgning, ikke en sikker automatisk identifikation af et produkt.

## Kontrol og reproduktion

```sh
python3 materials.py build
python3 materials.py verify
python3 -m unittest discover -s tests -v
python3 tests/verify_snapshot.py
```

Build gendanner SQLite fra JSONL og kontrollerer originalernes SHA-256, obligatoriske originale værditekster, endelige numeriske værdier, kilde-/materialereferencer og unikke ID'er. En fejlet import bevarer den tidligere database. Seks importer-/integritetstests er gennemført.

Alle 7.135 originalchecksums, SQLite-integritet og fremmednøgler er kontrolleret. Uafhængige udtrækskontroller sammenholder 150 tilfældigt valgte miljøværdier, 100 tekniske JSON-værdier og 2.635 danske Excel-værdier direkte med originalerne. Kildespecifikke kontroller er desuden beskrevet i de enkelte datasetdokumenter. Dette er teknisk integritet og udtrækskontrol, ikke en ny faglig certificering af alle kildeværdier.

## Fortolkning og videre integration

Originale enheder bevares. Beregningsværktøjerne understøtter nu eksplicitte SI-konverteringer og kildebestemte beregninger; databasen er ikke masseomregnet, og automatisk materialesammenlægning eller harmonisering af miljømetoder er ikke udført. Manglende data bliver ikke til nul. Kildebetingelser og kildeår er nødvendige ved konkret brug.

Datalicenser vurderes særskilt pr. kilde. Ukendte og afvigende vilkår er markeret; samlingen har ikke fået én ny fælles datalicens. Originaler med fri adgang er ikke automatisk frit genudgivelige.

CLI'et gør data tilgængelige for agenter. Der er nu leveret en [beregningsarbejdsgang med read-only modeladaptere](../workflows/modelberegninger.md), navnebaserede kandidatforslag, eksplicitte kildebindinger, enhedskonvertering og moduler til masse, klimabidrag og træfugt. En repository-agent-skill og10 modelcases er efterprøvet. Kandidater er ikke automatisk produktækvivalens; kildens anvendelighed skal stadig vurderes. Den [brede materialevision](../ideer/aaben-materialeplatform.md) gælder fortsat.

## Offentlig distribution og første installation

Hele det strukturerede snapshot følger med i Git som 15 Parquet-filer på 90.628.421 bytes. Alle tabeller, kolonner og 1.985.582 observationer er bevaret. `scripts/build_database.py` gendanner arbejdsdatabasen med kontrol af alle rækker, kontrolsummer, indekser og integritet. En færdig SQLite-download tilbydes også som versionsbundet Release-fil.

`materials.py verify --database-only` kontrollerer databasen uden at påstå kildefilverifikation. Originalfiler er separate; de relevante eksempelkilder kan hentes med `scripts/fetch_sources.py --demo`. Dette er ikke en demo-database: det er originaldokumenter til eksemplerne. Se [data og versionsmanifest](../../data/README.md) og [begynderguiden](../../docs/KOM-GODT-I-GANG.md).
