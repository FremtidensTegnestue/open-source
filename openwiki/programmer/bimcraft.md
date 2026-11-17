---
type: reference
title: "BIMcraft — bygningsmodeller og IFC"
description: "BIMcraft til bygningsmodellering, tegninger, IFC og automatisering med CLI og MCP."
tags: ["programs", "cad", "agents"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:09:45.141Z
sources:
  - id: openwiki-source-7f0ba6e7f2940bdf6fc642dc
    resource: repo://sources/programmer/bimcraft/cli-help.txt
  - id: openwiki-source-e978b8d96087eeccaeed02ed
    resource: repo://sources/programmer/bimcraft/README.md
  - id: openwiki-source-af5ac3680872a1b8fc55ee8d
    resource: repo://sources/programmer/installation.json
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# BIMcraft

BIMcraft er et open source-program skrevet i Rust til Building Information Modeling (BIM). Man modellerer en bygning som etager, vægge, døre, vinduer, dæk, tage, rum og andre bygningselementer med indbyrdes relationer. Ud fra modellen kan programmet arbejde med planer, snit, facader, 3D-visninger, tegningsark og skemaer.

## Hvad bruges det til?

BIMcraft er relevant til opbygning og gennemgang af bygningsmodeller og til udveksling af modeller via IFC. CLI'en kan inspicere projekter, tælle elementer, rapportere advarsler og konvertere filer. Hjælpeteksten beskriver import af IFC og Revit `.rvt` samt eksport til blandt andet IFC4, glTF/GLB, SVG og PNG.

Importstøtte er ikke i sig selv en garanti for, at alle oplysninger fra enhver Revit- eller IFC-fil gengives uden forskelle. Konkrete filer skal kontrolleres ved brug.

## Installeret på serveren

| Del | Version | Kommando |
| --- | --- | --- |
| App | 0.12.0 | `bimcraft` |
| CLI | 0.12.0 | `bimcraft-cli` |

Installationen er Linux ARM64. Versioner og pakkestatus blev kontrolleret den 17. november 2026. Projektformatet er `.bimc`; CLI-hjælpen angiver også støtte til ældre `.bimcraft`-filer.

## Agentadgang

Programmet stiller kommandoer til rådighed for både scripts og agenter. CLI'en kan arbejde uden et åbent appvindue. MCP-serveren kan arbejde med sit eget projekt eller forbinde til et projekt i en kørende app.

```sh
bimcraft-cli --version
bimcraft-cli commands
bimcraft-cli info model.ifc
```

`run` udfører kommandoer eller scripts og kan gemme resultatet; `convert` konverterer filer. `mcp --read-only model.ifc` er den dokumenterede indgang til en MCP-server, hvor agenten kan læse projektet uden at ændre det eller overskrive dets fil. Eksempelkommandoerne er dokumentation; der er ikke startet en MCP-server her.

## Forhold til arkivmaterialet

[Lisbjerg Bakke](../tools/lisbjerg-bakke.md) indeholder IFC-modeller, som er relevante kandidater til senere inspektion. Import af disse konkrete modeller er ikke testet i denne opgave. [AEFOROS](../tools/aeforos.md) og [LCC + Revit](../tools/lcc-revit.md) viser historiske arbejdsgange mellem BIM-data og beregninger; de er ikke integreret i BIMcraft her.

[Solidcraft](solidcraft.md) er det valgte værktøj til parametrisk CAD og 3D-modellering af emner og detaljer.

## Kilder og kontrolniveau

Beskrivelsen bygger på den installerede [README](../../sources/programmer/bimcraft/README.md), [CLI-hjælp](../../sources/programmer/bimcraft/cli-help.txt) og [installationsregistrering](../../sources/programmer/installation.json). Licens- og ophavsoplysninger er bevaret sammen med kilderne.

Officielle links: [repository](https://github.com/IPedrax/BIMCraft), [udgivelse 0.12.0](https://github.com/IPedrax/BIMCraft/releases/tag/v0.12.0).

Den oprindelige registrering kontrollerede versioner og hjælp. Der er siden leveret en [read-only adapter og beregningsarbejdsgang](../workflows/modelberegninger.md) med fem native modelcases og en kontrolleret IFC-import. Blandede materialelag er uafklarede. Gulvvolumener rapporteres i trin0,001m³ i CLI0.12.0; præcisionsgrænsen bevares i beregningerne. En GUI-brugertest er ikke udført.

## Installation til egen brug

Programmet installeres separat fra materialeværktøjet. [Hent hos den officielle udgiver](https://github.com/IPedrax/BIMCraft/releases/tag/v0.12.0), og følg [begynderguiden](../../docs/KOM-GODT-I-GANG.md) for opsætning og eksempelkommandoer. Dokumentationen ovenfor beskriver den afprøvede installation, ikke en automatisk installation på din computer.
