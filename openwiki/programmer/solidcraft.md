---
type: reference
title: "Solidcraft — parametrisk CAD"
description: "Solidcraft til parametrisk 3D-modellering, filudveksling og agentstyring via CLI og MCP."
tags: ["programs", "cad", "agents"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:09:45.141Z
sources:
  - id: openwiki-source-af5ac3680872a1b8fc55ee8d
    resource: repo://sources/programmer/installation.json
  - id: openwiki-source-cf936d3ab8b33198eee2f7fa
    resource: repo://sources/programmer/solidcraft/cli-help.txt
  - id: openwiki-source-37dc76fb1617b28fee214dee
    resource: repo://sources/programmer/solidcraft/README.md
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# Solidcraft

Solidcraft er et open source-program skrevet i Rust til parametrisk CAD og 3D-modellering. Man tegner skitser, angiver mål og geometriske bindinger og bygger solide emner gennem en historik af operationer. Når et mål ændres, kan modellen genberegnes ud fra denne historik.

## Hvad bruges det til?

Programmet er relevant til eksempelvis beslag, kabinetter, samlinger, konstruktionsdetaljer og dele til 3D-print. Skitser og parametre gør det muligt at fremstille varianter af samme emne. CLI'en kan arbejde med designfiler og STEP, eksportere modeller og danne billeder til geometrisk gennemgang. Hjælpeteksten beskriver blandt andet STL-, OBJ- og 3MF-eksport.

Solidcraft er brugerens valgte værktøj til CAD og 3D-modellering. Beskrivelser af en model bør fortsat skelne mellem geometrisk kontrol og fysisk afprøvet funktion.

## Installeret på serveren

| Del | Version | Kommando |
| --- | --- | --- |
| App | 0.44.0 | `solidcraft` |
| CLI | 0.44.0 | `solidcraft-cli` |

Installationen er Linux ARM64. Versioner og pakkestatus blev kontrolleret den 17. november 2026; oplysningerne beskriver denne installation, ikke en løbende garanti om nyeste version.

## Agentadgang

`solidcraft-cli` kan køre kommandoscripts, inspicere modeller og eksportere filer uden manuel betjening af appen. Den indbyggede MCP-server kan arbejde headless eller forbinde til en kørende app.

```sh
solidcraft-cli --version
solidcraft-cli commands
solidcraft-cli --help
```

`run` bruges til at udføre scripts og gemme eller eksportere resultatet; `eval`/`inspect` til inspektion; `snapshot` til billeder af geometrien. `mcp --headless` starter en selvstændig MCP-server. Det at programmet understøtter MCP betyder ikke, at en server er konfigureret eller startet i denne session.

## Forhold til de øvrige værktøjer

[BIMcraft](bimcraft.md) arbejder med bygningselementer og BIM-information. Solidcraft er relevant, når arbejdet vedrører parametriske emner og detaljer. Det beregner ikke automatisk de LCA- eller LCC-metoder, som findes i Vandkunsten-arkivet.

## Kilder og kontrolniveau

Beskrivelsen bygger på den installerede [README](../../sources/programmer/solidcraft/README.md), [CLI-hjælp](../../sources/programmer/solidcraft/cli-help.txt) og [installationsregistrering](../../sources/programmer/installation.json). De medfølgende licens- og ophavsoplysninger er bevaret sammen med kilderne.

Officielle links: [repository](https://github.com/tangency-labs/solidcraft), [dokumentation](https://docs.solidcraft.io/), [udgivelse 0.44.0](https://github.com/tangency-labs/solidcraft/releases/tag/v0.44.0).

Den oprindelige programregistrering kontrollerede versioner og hjælp. Der er siden leveret en [read-only adapter og beregningsarbejdsgang](../workflows/modelberegninger.md), som bruger faktisk målte lukkede kroppes volumen. Fem materiale-kontrolcases og et ekstra træfugtemne er gennemført; en faktisk CAD-snapshot findes i [kontrolrapporten](../../docs/VALIDATION.md). En GUI-brugertest er ikke udført. Standardmaterialet behandles som ukendt, og total overflade bruges ikke som referenceareal.

## Installation til egen brug

Programmet installeres separat fra materialeværktøjet. [Hent hos den officielle udgiver](https://solidcraft.io/download/), og følg [begynderguiden](../../docs/KOM-GODT-I-GANG.md) for opsætning og eksempelkommandoer. Dokumentationen ovenfor beskriver den afprøvede installation, ikke en automatisk installation på din computer.
