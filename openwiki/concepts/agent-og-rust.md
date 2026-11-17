---
type: reference
title: "Muligt genbrug i Rust og agentværktøjer"
description: "Afgræns fremtidig videreudvikling ud fra de faktiske kilder og kendte verifikationsbehov."
tags: ["agents", "rust", "modernization"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T20:32:16.998Z
sources:
  - id: openwiki-source-16ad9c57da182f87c66c86c2
    resource: repo://catalog/coverage.json
  - id: openwiki-source-ad4b3c306dd228fe019c57fc
    resource: repo://extracted/opensource.vandkunsten.com/03_earlybird-lca/index.txt
generated: { by: "codex", at: "2026-11-17T20:32:16.998Z" }
---

# Muligt genbrug i Rust og agentværktøjer

## Nuværende udgangspunkt

Samlingen består af selvstændige værktøjer og projektmateriale med forskellige platforme. Der er nu en Python-beregningsmotor og et JSON-CLI; der er ikke implementeret en fælles Rust-beregningskerne eller en ny MCP-server. De maskinlæsbare kataloger gør materialet lettere at finde, men udgør ikke validerede beregningsværktøjer.

Excel-formler og fanestruktur er tilgængelige som JSON/CSV. Originale VBA-projekter og binære Grasshopper-filer er bevaret, men ikke fuldt oversat til tekst. En agent skal derfor kunne skelne mellem inspiceret beregningslogik og blot arkiveret binært materiale.

## Leveret datagrundlag

Der er nu en samlet [materialedatabase med originalkilder og JSON-CLI](../data/materialedatabase.md). Collectors og databasebygger er implementeret i Python; SQLite kan også læses fra Rust. Der er nu også [modeladaptere, beregningsmoduler og en agent-skill](../workflows/modelberegninger.md); en fælles Rust-beregningskerne er ikke implementeret. Den oprindelige arkivkatalogisering og den nye materialedataindsamling er forskellige leverancer.

## Gældende produktretning

Brugerens valgte retning er en [åben materialedataplatform](../ideer/aaben-materialeplatform.md) med så mange relevante og dokumenterede datapunkter som muligt på tværs af materialer og egenskaber. Database, beregningsmoduler, CLI, agent-skills og integration med BIMcraft og Solidcraft skal gøre grundlaget anvendeligt for AI-agenter. Træværktøjet, en ydervæg eller facadebeklædning er eksempler og historiske referencekilder, ikke projektets vedtagne afgrænsning.

[Idékataloget](../ideer/danske-arkitektvaerktoejer.md) beskriver mulige anvendelser af dette fælles grundlag.

## Genbrug af eksisterende beregningsmetoder

De historiske værktøjer kan undersøges og genbruges, hvor de bidrager til den brede platform. Det omfatter træberegnerens forudsætninger og formelforskelle, EarlyBirds geometri og aggregerede data, LCA estimators cases og matchmetode samt AEFOROS/LCC's materialekobling og eksportkontrakter. En tidligere foreslået rækkefølge med træværktøjet først er ikke en bindende udviklingsplan eller en begrænsning af datadækningen.

## Mulig agentkontrakt

De leverede `calculate`- og `assess`-kommandoer modtager eksplicitte datavalg og returnerer resultat, enheder, antagelser, kildeidentitet, metodeversion og uafklarede forhold. En agent bør kunne afprøve scenarier uden at redigere originalfiler eller opfinde materialeværdier. CLI og en repository-agent-skill er etableret; en særskilt MCP-adapter er ikke leveret.

Den centrale verifikation er beregningsmæssig ækvivalens på udvalgte referencecases. En vellykket port til Rust viser ikke alene, at historiske datasæt eller faglige modeller er tilstrækkelige til nye projekter. EarlyBirds side beskriver eksempelvis data fra 2015 og afvigelser i oprindelige sammenligninger.

## Videre arbejde

Kortlæg kilder, materialefamilier, egenskaber, enheder, anvendelsesbetingelser og dokumentationsniveau på tværs af hele ambitionen. Brug dokumenterede referenceeksempler til at kontrollere dataudtræk, beregninger og modelkoblinger. Konkrete kontrolcases fastlægger ikke et snævrere produktomfang. De arkiverede beregningsmetoder er ikke ændret i denne wikiopdatering.
