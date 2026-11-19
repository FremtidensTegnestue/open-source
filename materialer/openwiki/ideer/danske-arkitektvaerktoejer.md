---
type: proposal
title: "Open source-værktøjer til danske arkitekter"
description: "Seks forslag med brugsværdi, prioritering, agentadgang og integration med Solidcraft og BIMcraft."
tags: ["ideas", "architecture", "agents", "rust", "bim"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T19:33:55.632Z
sources:
  - id: openwiki-source-d9955c06fdc484206d8845a1
    resource: repo://extracted/opensource.vandkunsten.com/07_FBABLisbjerg/index.txt
  - id: openwiki-source-e978b8d96087eeccaeed02ed
    resource: repo://sources/programmer/bimcraft/README.md
  - id: openwiki-source-cf936d3ab8b33198eee2f7fa
    resource: repo://sources/programmer/solidcraft/cli-help.txt
generated: { by: "codex", at: "2026-11-17T19:33:55.632Z" }
---

# Open source-værktøjer til danske arkitekter

Dette er et idékatalog og et forslag til prioritering. Værktøjerne nedenfor er ikke implementeret. Retningen er en dansk værktøjskasse, der forbinder modeller, materialer og dokumentation, så arkitekten kan undersøge konsekvenserne af ændringer, mens projektet stadig kan ændres.

## Fælles grundlag: den åbne materialeplatform

Brugerens aktuelle produktretning er en [bred materialedataplatform](aaben-materialeplatform.md) med database, beregninger, CLI, agent-skills og integration med BIMcraft og Solidcraft. Målet er så mange relevante, dokumenterede datapunkter som muligt på tværs af materialer og egenskaber. Forslagene nedenfor er mulige anvendelser; rækkefølgen udgør ikke en vedtaget afgrænsning eller udviklingsplan.

## Seks værdifulde værktøjer

| Prioritet | Værktøj | Konkret værdi | Mulig integration |
| --- | --- | --- | --- |
| 1 | Modeltjek og mængdekontrol | Find manglende materialer, uklare enheder, ufuldstændige bygningsdele og forskelle mellem modelversioner. Vis, hvilke mængder der er tilstrækkeligt dokumenterede til videre beregninger. | BIMcraft og IFC |
| 2 | Dansk konstruktionsbibliotek | Genbrug vægge, dæk, tage og facader med lag, tykkelser, materialer, kilder og miljødata. Brug samme konstruktion i model, beregning og beskrivelse. | BIMcraft til bygningsdele; Solidcraft til parametriske detaljer |
| 3 | Klima- og variantværktøj | Sammenlign konstruktionsvalg og forklar forskelle i klimapåvirkning, mængder og forudsætninger. | Materialer og mængder fra begge programmer |
| 4 | Dansk grund- og projektbrief | Saml relevante ejendomsoplysninger, plangrundlag, terræn og eksisterende bygninger i et kildebelagt projektgrundlag. | Dokumentation først; senere placering og projektparametre i BIMcraft |
| 5 | Renoverings- og genbrugsplanlægger | Registrér, hvad der bevares, udskiftes eller demonteres. Sammenlign scenarier, og synliggør manglende undersøgelser og registreringer. | BIMcraft og IFC |
| 6 | Parametriske konstruktionsdetaljer | Generér varianter af eksempelvis træbeklædning, samlinger og beslag med eksplicitte mål og frigange. Levér model, illustration og stykliste. | Solidcraft |

Prioriteringen er en vurdering af mulig brugsværdi, ikke en dokumenteret markedsundersøgelse. Datadækning og anvendelsesvilkår for danske kilder skal undersøges for de valgte funktioner.

## Foreslået kerneprodukt

Kombinér modeltjek, konstruktionsbibliotek og variantberegning. Det kan samle arbejde, som ellers fordeles mellem model, regneark, produktdatablade og rapport.

Et eksempel på en fremtidig agentopgave:

> Sammenlign vores nuværende ydervæg med to alternativer. Bevar væggens samlede tykkelse, vis klimaforskellen og fortæl, hvilke oplysninger der mangler.

Den foreslåede arbejdsgang er:

1. Læs væggenes typer, lag og mængder.
2. Find relevante konstruktioner i biblioteket.
3. Kontroller enheder og match mellem materialer og datasæt.
4. Beregn sammenlignelige alternativer med samme afgrænsning.
5. Vis resultater, antagelser, kildehenvisninger og manglende oplysninger.
6. Opret et valgt alternativ som en separat modelvariant, når brugeren ønsker det.

## Integration med Solidcraft og BIMcraft

[BIMcraft](../programmer/bimcraft.md) har dokumenterede kommandoer til bygningsdele, materialelag, projektparametre og skemaer samt IFC, CLI og MCP. Det er et konkret udgangspunkt for at læse modeldata og oprette varianter. Om de nødvendige mængder er komplette og korrekte, skal undersøges på konkrete modeller; en dokumenteret kommando er ikke en valideret integration.

[Solidcraft](../programmer/solidcraft.md) understøtter scripts og MCP både headless og forbundet til appen. Det giver en indgang til parametriske detaljer, geometrisk inspektion og eksport. Solidcraft bruges til CAD og 3D-modellering i dette arbejde. Geometrisk kontrol og fysisk afprøvet funktion skal fortsat holdes adskilt.

Den foreslåede fordeling af ansvar er, at programmerne ejer modellerne, mens vores værktøjer ejer beregninger, datakilder og dokumentation:

**Model → kontrollerede mængder → beregning → dokumenteret resultat → eventuel modelændring.**

Et muligt teknisk udgangspunkt er et fælles Rust-bibliotek, et lille CLI og JSON-input/output med eksplicitte enheder. MCP kan eksponere de samme funktioner for agenter. IFC og andre adaptere kan senere forbinde andre modelleringsprogrammer. Ingen af disse nye integrationer er bygget i denne opgave.

## Det danske særkende

Værdien bør ligge i danske konstruktionspraksisser, relevante projektoplysninger, dokumenterede materialedata og tydelige beregningsforudsætninger. Kilder, hentetid, metodeversion og dataversion skal kunne følges fra resultatet tilbage til grundlaget.

En senere regelkontrol skal skelne mellem konstaterede afvigelser, manglende dokumentation og forhold, der kræver faglig vurdering. Den skal ikke udlede et ubetinget godkendelsesstempel fra ufuldstændige modeldata.

## Genbrug af Vandkunsten-materialet

- [EarlyBird LCA](../tools/earlybird-lca.md) og [AEFOROS](../tools/aeforos.md) er udgangspunkter for at undersøge klimaoverslag, materialematch og sammenhæng med BIM-mængder.
- [LCA estimator](../tools/lca-estimator.md) giver en anden tilgang: match mod dokumenterede bygningscases.
- [Træværktøjet](../tools/trae-udvidelse.md) er en konkret reference for en mulig beregningsport, når forudsætninger og formelforskelle er afklaret.
- [Lisbjerg Bakke](../tools/lisbjerg-bakke.md) indeholder konkrete IFC-modeller, tegninger og detaljer til en første undersøgelse.

Historiske metoder og data er referencegrundlag. En omskrivning til Rust opdaterer ikke automatisk datagrundlag eller dokumenterer faglig egnethed. Licensobservationerne fremgår af [rettighedssiden](../archive/rettigheder.md).

## Eksempler til at efterprøve løsningen

Lisbjerg-materialet, konkrete bygningsdele og Vandkunstens regneark kan bruges som referencecases for modeludtræk, materialematch og beregninger. Manglende oplysninger skal dokumenteres, og resultater skal kunne følges tilbage til modelobjekter, materialedata og kilder.

Disse cases begrænser ikke platformen til én bygning, én ydervæg eller facadebeklædning. Den brede ambition og de fælles arbejdsspor er beskrevet i [materialeplatformens vision](aaben-materialeplatform.md). [Rust- og agentanalysen](../concepts/agent-og-rust.md) forbinder retningen med de arkiverede beregningsværktøjer.

## Grundlag

De eksisterende tekniske muligheder er beskrevet i de bevarede [BIMcraft-kilder](../../sources/programmer/bimcraft/README.md), [BIMcrafts CLI-hjælp](../../sources/programmer/bimcraft/cli-help.txt), [Solidcrafts README](../../sources/programmer/solidcraft/README.md) og [Solidcrafts CLI-hjælp](../../sources/programmer/solidcraft/cli-help.txt). Vandkunsten-materialets status findes i [projektregisteret](../../catalog/projects.json). Resten af siden beskriver foreslået produktadfærd og arbejde, der endnu skal afprøves.
