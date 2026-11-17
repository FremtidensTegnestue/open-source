---
type: proposal
title: "Åben materialedataplatform for arkitekter og AI-agenter"
description: "Ambitiøs vision for bred indsamling af materialeegenskaber og et fælles data- og beregningsgrundlag med CLI, agent-skills og BIM/CAD-integration."
tags: ["materials", "data", "agents", "vision", "calculations"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T20:32:16.998Z
sources:
  - id: openwiki-source-81ad6b5f4c049458a07c965f
    resource: repo://sources/produktvision/materialeplatform.md
generated: { by: "codex", at: "2026-11-17T20:32:16.998Z" }
---

# Åben materialedataplatform for arkitekter og AI-agenter

## Vision

Vi vil samle så mange relevante, dokumenterede datapunkter om byggematerialer som muligt og gøre dem anvendelige gennem en database, beregningsværktøjer, CLI og agent-skills. AI-agenter skal kunne forbinde oplysninger fra BIMcraft- og Solidcraft-modeller med materialedata, udføre beregninger og forklare resultaterne.

Ambitionen omfatter hele materialelandskabet og mange faglige egenskaber. Træ og facadebeklædning er mulige anvendelser blandt mange. Projektet har ingen vedtaget afgrænsning til én materialefamilie, én bygningsdel eller Vandkunstens eksisterende værktøjer.

Denne side beskriver brugerens valgte brede produktretning. Et første [datagrundlag, SQLite-database og JSON-CLI](../data/materialedatabase.md) er nu leveret. Der er nu også leveret [kildebaserede beregninger, read-only modeladaptere og en agent-skill](../workflows/modelberegninger.md) med dokumenterede kontrolcases.

## Hvilke materialer og datapunkter?

Målet er bred dækning af generiske materialer, konkrete produkter, genbrugte materialer, sammensatte produkter og dokumenterede konstruktioner. Materialefamilier kan eksempelvis være træ og træprodukter, beton, mørtel, tegl, sten, metaller, glas, isolering, gips, plader, plast, biobaserede materialer, membraner, overfladebehandlinger, klæbere og befæstelser. Listen er åben for udvidelse.

| Dataområde | Eksempler på oplysninger, vi vil kunne registrere |
| --- | --- |
| Klima og miljø | EPD'er, GWP/CO2-ækvivalenter, øvrige miljøindikatorer, livscyklusmoduler, energiforbrug, ressourceforbrug og affald |
| Fysiske egenskaber | Densitet, vægt, dimensioner, porøsitet, fugtindhold og tolerancer |
| Fugt og temperatur | Svind, kvældning, termisk udvidelse, fugtoptagelse, diffusion og sorptionsdata |
| Varme | Varmeledningsevne, varmekapacitet og betingelserne for værdierne |
| Mekanik | Styrke, stivhed, elasticitet, deformation og retningsafhængighed |
| Brand | Dokumenterede klassifikationer, prøvningsforhold og tilknytning til konkrete produkter eller konstruktioner |
| Akustik | Lydabsorption, lydisolering og de konstruktioner eller prøvningsopstillinger, resultaterne gælder for |
| Holdbarhed | Levetidsforudsætninger, vedligehold, eksponeringsforhold og nedbrydning |
| Sundhed og indhold | Stoffer, emissioner og dokumenterede sundheds- eller indeklimaoplysninger |
| Cirkularitet | Genanvendt indhold, genbrug, adskillelse, sporbarhed og behandlingsmuligheder |
| Praktisk anvendelse | Montering, samlinger, kompatibilitet, anvendelsesbegrænsninger og relevante produktvejledninger |
| Forsyning og økonomi | Dokumenterede prisobservationer, tilgængelighed, geografi og tidspunkt, hvor data må anvendes |
| Identitet | Materialenavne, synonymer, produktnavne, producent, klassifikationer, identifikatorer og relationer |

Dette er ønsket datadækning, ikke en påstand om, at oplysningerne allerede findes samlet eller kan sammenlignes direkte. En egenskab kan gælde et generisk materiale, et bestemt produkt, en samling eller en hel bygningsdel. Datamodellen skal bevare den forskel.

## Data skal kunne spores og forstås

Databasen skal kunne rumme flere værdier og dokumenterede uenigheder. Den skal bevare mindst:

- Original kilde, dokumentversion, præcis henvisning og hentetid.
- Værdi, enhed, interval, usikkerhed og eventuel målemetode.
- Om oplysningen er målt, deklareret, beregnet, typisk eller antaget.
- Gyldighed, geografi, produktidentitet og anvendelsesbetingelser.
- Relevante forhold som temperatur, fugt, materialeretning, tykkelse og sammensætning.
- For miljødata: deklareret enhed, livscyklusmoduler, metode og øvrige nødvendige afgrænsninger.
- Licens, ophav, adgangsvilkår og hvad vi må lagre og videreudgive.
- Relation til originaldata samt log over rettelser, normalisering og udskiftede versioner.

Vi vil bevare rå kilder, strukturerede originalværdier og normaliserede værdier, så en enhedsomregning eller materialekobling kan efterprøves. Et ukendt felt skal kunne forblive ukendt. Datadækning må ikke forveksles med sikkerheden i det enkelte tal.

## Kilder og indsamling

Vandkunsten er et udgangspunkt. Den bredere indsamling skal undersøge miljødatabaser og EPD-programmer, producentdokumentation, forskningspublikationer, offentlige datasæt, tekniske vejledninger og andre dokumenterede materialekilder.

Datakilder skal katalogiseres med emnedækning, adgangsform, opdateringsmuligheder, datakvalitet og vilkår. Åben adgang til et dokument indebærer ikke automatisk fri videreudgivelse af alle tabeller eller standardtekster. Hvor kildedata ikke må kopieres, skal platformen kunne gemme henvisninger og tilladte metadata.

Ambitionen er løbende at øge både antal datapunkter, materialedækning og brugbarhed. Målinger kan omfatte antal kilder, materialer, produkter, egenskaber, komplette datapunkter med proveniens samt friske og fagligt kontrollerede poster. Ingen bestemt totalmængde er endnu lovet.

## Database, beregninger, CLI og skills

| Del | Ansvar |
| --- | --- |
| Database | Søge, identificere, sammenholde og hente dokumenterede materialedata og relationer |
| Beregningsmotor | Anvende eksplicitte formler og metoder med kontrol af enheder og forudsætninger |
| CLI | Gøre søgning, opslag, sammenligning, validering og beregning tilgængelig for agenter og programmer |
| Agent-skills | Forklare materialevalg, datavalg, arbejdsgange, brug af modeller og håndtering af mangler |
| Modeladaptere | Hente modeloplysninger og koble objekter, materialer og mængder til databaseposter |
| MCP-adgang | En mulig yderligere indgang til de samme funktioner fra agentklienter |

Den leverede database bruger SQLite, og CLI, adaptere og beregningsmoduler er implementeret i Python. Rust er fortsat en mulig senere implementation; det er ikke et krav om omskrivning af det fungerende grundlag. JSON-input/output, stabile identifikatorer, eksplicitte enheder og versionsbundne resultater skal gøre løsningen anvendelig på tværs af programmer.

AI-agenten finder relevante oplysninger, vælger værktøjer og forklarer resultatet. Efterprøvbar programkode udfører selve beregningerne. Agent-skills skal eksempelvis hjælpe agenten med at opdage, når et materialematch eller en omregning kræver flere oplysninger.

## Beregningsambition

Platformen skal kunne udvides med mange beregningsområder: mængder og masse, klima og øvrige miljøpåvirkninger, fugt- og temperaturbevægelse, varmeegenskaber, levetid og vedligehold samt sammenligning af produkter og konstruktioner.

Mekaniske, brandtekniske og akustiske data skal kunne indgå, når der findes en egnet metode og tilstrækkelige oplysninger. En klassifikation eller materialeegenskab er ikke alene en fuld beregning af en bygningsdels ydeevne. Hvert beregningsmodul skal derfor beskrive input, metode, anvendelsesområde, output og kontrolgrundlag.

Resultater skal indeholde kildehenvisninger, anvendte værdier og omregninger, antagelser, metode- og dataversioner, mangler og relevante usikkerheder. Høj datamængde og faglig efterprøvbarhed skal udvikles sammen.

## Integration med BIMcraft og Solidcraft

Den ønskede arbejdsgang er:

1. Agenten læser modeloplysninger gennem programmernes dokumenterede CLI- eller MCP-grænseflader.
2. Adapteren identificerer objekter, materialer, lag, dimensioner og tilgængelige mængder.
3. Oplysningerne kobles til relevante databaseposter med synlig begrundelse og eventuelle alternative matches.
4. Værktøjerne kontrollerer enheder, anvendelsesbetingelser og nødvendige manglende oplysninger.
5. Beregningsmotoren udfører den valgte beregning eller scenariesammenligning.
6. Agenten forklarer resultatet med forbindelse tilbage til modelobjekter og kilder.
7. Resultater kan senere eksporteres som data og dokumentation eller knyttes til modelobjekter gennem en verificeret integration.

[BIMcraft](../programmer/bimcraft.md) er en indgang til bygningsmodeller, lag og bygningsdele. [Solidcraft](../programmer/solidcraft.md) er indgangen til parametrisk CAD og 3D-modellering af emner og detaljer. Det er programmernes dokumenterede adgangsmuligheder, der gør integrationen relevant; read-only adaptere og konkrete kontrolmodeludtræk er nu bygget og afprøvet, med de dokumenterede præcisions- og materialebegrænsninger.

Et eksempel på en fremtidig opgave er: “Undersøg materialerne i denne model. Beregn de forhold, der er tilstrækkeligt belyst, sammenlign relevante alternativer og vis, hvilke oplysninger der mangler.” Eksemplet gælder på tværs af materialer og bygningsdele.

## Udviklingsretning og status

Arbejdssporene er kildekatalog og dataindsamling, fælles datamodel, normalisering og kvalitet, beregningsmoduler, CLI, agent-skills samt modeladaptere. Konkrete eksempler bruges til at kontrollere sammenhængen gennem hele løsningen og fastlægger ikke en permanent begrænsning af datadækningen.

[Idékataloget til danske arkitekter](danske-arkitektvaerktoejer.md) beskriver mulige anvendelser oven på dette fælles grundlag. [Rust- og agentanalysen](../concepts/agent-og-rust.md) beskriver genbrug af de historiske værktøjer.

Den første materialedatabase er nu bygget med bred dataindsamling, bevarede originalkilder og et CLI til opslag og kontrol. Den aktuelle [databaseside](../data/materialedatabase.md) dokumenterer dækning, kvalitet og anvendelse. Kildebaserede beregningsmoduler, read-only BIM/CAD-adaptere og en repository-agent-skill er nu leveret og efterprøvet. Materialematch er kandidatforslag med eksplicit datavalg; automatisk produktækvivalens og yderligere metoder er fortsat videre arbejde. Datadækningen skal udvides i tråd med den brede ambition.

Grundlaget for retningen er [brugerens projektbrief](../../sources/produktvision/materialeplatform.md). De arkiverede materialer og programmernes dokumentation er konkrete udgangspunkter for det næste arbejde.
