---
type: workflow
title: "Fra model til dokumenteret materialeberegning"
description: "Afprøvet CAD-til-BIM-overførsel, eksplicitte materialebindinger og kildebaserede beregninger med modelændring og geometrisk returkontrol."
tags: ["workflow", "calculations", "agents", "models", "units"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-3563321954696628d81e0f45
    resource: repo://adapters/bimcraft.py
  - id: openwiki-source-5a211c6a3b6dfbffd3a327df
    resource: repo://data/releases/publication-validation.json
  - id: openwiki-source-048984dcfeb6efe6cfd028de
    resource: repo://docs/CALCULATIONS.md
  - id: openwiki-source-b3110af0301aaa7b45f546f7
    resource: repo://examples/integrated-workflow/README.md
  - id: openwiki-source-94beeb3c6c01fba424f773e6
    resource: repo://examples/integrated-workflow/verification.json
  - id: openwiki-source-f14a5c8262e08b3c5ca3d457
    resource: repo://examples/reports/workflow-verification.json
  - id: openwiki-source-e1a7bac04543834c53055133
    resource: repo://tests/test_bimcraft_adapter.py
  - id: openwiki-source-7d5f2d1c7128a5797ab846d7
    resource: repo://tests/test_bimcraft_mesh_quantities.py
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# Fra model til dokumenteret materialeberegning

Den leverede arbejdsgang kan læse faktiske Solidcraft- og BIMcraft-modeller og beregne vægt, kildebestemte klimabidrag pr. modul og træets fugtbevægelse. Hvert resultat bevarer modelhash, datavalg, kildehenvisninger, enheder og anvendelsesbetingelser.

## Arbejdsgang for en agent

1. `extract` læser modellen og viser materialer, programafledte mængder og advarsler.
2. `suggest` giver navnebaserede kandidater fra databasen. Et kandidatfund er ikke en fastslået produktækvivalens.
3. Datavalg gennemgås med `show`, `observations` og `sources`. Bindingen angiver konkrete materiale- og observation-ID'er, modellens hash, materialenavn og en forklaring på valget.
4. `assess` udfører valgte beregninger på den modelbundne konfiguration og skriver en JSON-rapport.

```sh
python3 materials.py extract examples/models/solidcraft/solid-wood.sc --software solidcraft --out /tmp/model.json
python3 materials.py suggest examples/models/solidcraft/solid-wood.sc --software solidcraft --out /tmp/kandidater.json
python3 materials.py assess examples/models/solidcraft/solid-wood.sc --software solidcraft --bindings examples/bindings/solidcraft-solid-wood.json --out /tmp/beregning.json
python3 materials.py assess examples/models/bimcraft/controls.bimc --software bimcraft --bindings examples/bindings/bimcraft-controls.json --out /tmp/bim-beregning.json
```

Se [beregningsguiden](../../docs/CALCULATIONS.md) for bindingsformat, metoder, enheder og fejlstatus. Repositoryet indeholder en [agent-skill](../../.agents/skills/material-model-assessment/SKILL.md), som er efterprøvet af en separat agent gennem friske model- og databaseopslag.

## Metoder og ejerskab

`material_calculations.py` ejer kildebaseret skalering og formler. `material_units.py` ejer eksplicitte enhedskonverteringer. `adapters/solidcraft.py` og `adapters/bimcraft.py` læser modeller uden at gemme dem. `materials.py` eksponerer arbejdsgangen som JSON-CLI. `report_io.py` beskytter modeller, input og originalarkiv ved atomisk rapportskrivning.

Masse er volumen gange densitet. Klimabidrag skalerer den konkrete GWP-observation til faktisk mængde med kildens deklarerede enhed og mængde; eksempelvis er1ton og1000kg samme metriske reference, ikke1kg. Indikatorer og livscyklusmoduler holdes adskilt. En arealbasis med yderligere R- eller årsbetingelser er ikke en simpel arealskalering.

Træets fugtbevægelse følger USDA2021 ligning13–3 med en konkret arts-/retningskoefficient og begge fugttilstande inden for kildens interval. Modelakse/fiberretning er en eksplicit antagelse og kan ikke bestemmes af en boundingbox alene.

## Efterprøvning

[Kontrolrapporten](../../docs/VALIDATION.md) og [den maskinlæsbare sammenfatning](../../examples/reports/validation-summary.json) dokumenterer10 faktisk gemte modelcases: fem fra hver app og fem materialefamilier. Der er kontrolleret10 vægte og40 særskilte klimamodulresultater mod analytiske mål og original Excel. Et ekstra Solidcraft-træemne følger USDA's fugteksempel og giver1,7052mm breddeændring.

Det oprindelige kontrolforløb dokumenterer 40 beståede automatiske tests. En separat agent har fulgt skillen uden eksisterende eksempelbindinger og kontrolleret et faktisk stålemne mod originaltabellen. Se [samlet verifikation](../../examples/reports/workflow-verification.json) og [agentens konkrete kontrol](../../examples/agent-forward-test/independent-check.json).

```sh
python3 examples/run_controls.py
python3 -m unittest discover -s tests -v
```

## Præcision og uafklarede forhold

Solidcrafts standardmateriale behandles som ukendt. Total overflade er ikke automatisk et facade- eller referenceareal. BIMcraft0.12.0 rapporterer gulvvolumen i trin0,001m³; denne afrundingsgrænse føres videre til masse og klima. Det er ikke et samlet usikkerhedsinterval for materialernes egenskaber.

Blandede materialelag bliver uafklarede, og manglende input bliver ikke nul. Importadvarsler om udeladt indhold giver delvis status. Resultaterne er eksplicitte referencescenarier, ikke en automatisk as-built- eller myndighedsvurdering. En skill eller adapter betyder ikke, at en MCP-server er sat op i brugerens klient.

Den brede [materialeplatform](../ideer/aaben-materialeplatform.md) og [databasen](../data/materialedatabase.md) består fortsat på tværs af materialer og egenskaber; kontrolcases afgrænser ikke den videre dækning.

## Afprøvning på Lisbjerg Bakke

[Projektrapporten og bilagene](../../reports/lisbjerg-bakke/README.md) afprøver arbejdsgangen på de originale IFC2X3-modeller. KON giver blandt andet 75 trædæk med 354,568m³ og 20 betondæk med 209,709m³ som rapporterede, afrundede BIMcraft-mængder. Der er ingen godkendte projektprodukt-/EPD-bindinger og ingen samlet bygnings-LCA.

Importens `skipped`, `generic` og `moved` bevares nu i `extraction.import_summary`. Udeladelser og generiske repræsentationer giver selvstændige advarsler; tom `inspect.warnings` betyder ikke, at importen er komplet. Lisbjerg-udvidelsen havde en regressionstest, og dette forløb bestod med 41 tests. Manglende nettovolumen i den undersøgte CLI er en adgangs-/metodebegrænsning og beviser ikke, at den originale IFC-geometri mangler.

Rumvolumen og åbninger er ikke materialemængder. ARK/KON holdes adskilt, indtil koordinater, fagligt overlap og samlings-/delobjekter er afstemt. Rapportens betonberegning er et udtrykkeligt C25/30-referencescenarie, ikke et verificeret projektmateriale. Se [caseguiden](../tools/lisbjerg-bakke.md) for resultater, dokumentation og prioriterede afklaringer.

## Samlet Solidcraft → BIMcraft → materialeforløb

[Det dokumenterede forsøg](../../examples/integrated-workflow/README.md) overfører en faktisk Solidcraft-model med en udsparing og tre dele til BIMcraft gennem GLB, beregner fra begge programmer og kontrollerer en geometrisk returimport. Modellen bliver ikke tegnet igen i BIMcraft, og BIM-volumener kopieres ikke fra CAD.

BIMcrafts `import_mesh` giver generiske familier. Det nye aktive tilvalg `--mesh-quantities` til `extract`, `suggest` og `assess` læser de relevante `family`-trekanter og beregner nettovolumen for én understøttet, lukket og sammenhængende skal. Ikke-understøttede familier, åbne skaller og fejl i fladeretning bliver uafklarede. Metoden har afgrænset referenceplans-/placeringsstøtte og kontrollerer ikke generelt selvskæring. Standardadfærden er uændret.

Forsøget omfatter en betonplade på 1.500×1.000×100 mm, et hul på 300×200 mm og to stålskinner på 1.000×80×10 mm. Ændring til 120 mm plade giver 335,984→400,6688 kg og 55,28984→62,23064 kgCO₂e for A1–A3 i det eksplicitte referencescenarie. Begge programforløb stemmer med analytiske mål og original Excel. Alle overførte trekanter er uafhængigt sammenholdt med friske BIMcraft-udtræk, og returmodellerne er lukkede med kontrollerede placeringer og volumener.

De fulde materialenavne følger i dette eksempel med som visuelle GLB-navne. Database-ID’er, densitet, klimafaktorer og beregningsbindinger fastlægges gennem et eksplicit materialekort. På returen bliver fysiske materialer `Default`, og CAD-historikken følger ikke med GLB. Derfor gælder returkontrollen geometri; standardvægten bruges ikke som fysisk resultat.

Hver revision får et nyt BIM-projekt, fordi genimport tilføjer komponenter. Begge versioner har tre dele. Manglende bindinger giver ingen masse-/klimatal; gamle bindinger afvises mod ændrede modelhashes. Ved det integrerede forsøg bestod testsuiten med 54 tests, heraf 13 nye meshkontroller. Se [reproduktion, modeller og maskinlæsbare resultater](../../examples/integrated-workflow/README.md).

## Kør fra den offentlige Git-pakke

Følg [begynderguiden](../../docs/KOM-GODT-I-GANG.md): installer Python-pakker, gendan hele SQLite-databasen fra de medfølgende Parquet-filer, og prøv først et simpelt opslag eller en kendt mængde. De originale eksempeldokumenter kan hentes med `scripts/fetch_sources.py --demo`. Modeludtræk kræver de særskilte SolidCraft-/BIMCraft-CLI'er.

Den offentlige pakke er prøvet fra et rent udtræk af Git-filerne uden det lokale råarkiv. Databygning, 65 tests, beregningseksemplet og det integrerede CAD/BIM-ændringsforløb bestod. Se [publiceringskontrollen](../../data/releases/publication-validation.json).
