---
type: guide
title: Hvordan sammenligner vi klima, levetid og økonomi?
description: Sammenlign renovering og nybyg med samme funktion, tydelige mængder, energiforbrug, tidshorisont og udgifter.
tags: [life-cycle-assessment, life-cycle-costing, service-life, uncertainty]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-19T07:19:29.468Z
sources:
  - id: openwiki-source-db86dd5bd1f178d128948a17
    resource: repo://kilder/README.md
  - id: openwiki-source-6314359a6bfa04d8acc9cf03
    resource: repo://oplaeg/forste-besigtigelse.md
generated: { by: "codex", at: "2026-11-19T07:19:29.468Z" }
---

# Hvordan sammenligner vi klima, levetid og økonomi?

Et nyt vindue kan have et mindre varmetab end det gamle. Om udskiftning er et bedre valg end reparation med forsats, afhænger også af fremstillingen, hvor længe det gamle vindue kan holde, og hvor meget varme der faktisk spares. Arkitekten har brug for at kunne vise, hvilken af de antagelser der bærer resultatet.

## Sæt alternativerne op på samme grundlag

| Aftal først | Et brugbart svar |
| --- | --- |
| Hvilket behov skal dækkes? | Fx det samme antal brugbare boliger med samme adgang og sammenlignelig komfort. Hvis flere boliger eller mere opvarmet areal opstår, angiv både totalen og resultat pr. enhed. |
| Hvad ville ellers ske? | Beskriv fortsat drift og nødvendig vedligehold af det eksisterende som udgangspunkt. Sammenhold med reparation, mere omfattende transformation og, hvor det er et reelt alternativ, nedrivning og nybyg. |
| Hvilken periode og hvilke processer? | Vælg fælles periode. Angiv produktion, klargøring, transport, byggeplads, drift, kommende udskiftninger og afslutning, og vis eventuelle fravalg. |
| Hvilke data er målt? | Angiv enhed, mængde, oprindelse, dato og usikkerhed. Registrér varmekilde, faktisk brug, areal og periode for energidata. Brug samme energiforudsætninger på tværs af alternativer. |

**LCA** er en livscyklusvurdering af miljøpåvirkninger. Ved et klimaregnskab angives klimapåvirkning typisk i kg CO₂-ækvivalenter. Vis det bidrag, der kommer ved indgrebet nu, sammen med senere bidrag fra drift og udskiftning. Oplys særskilt, hvordan brugte dele, bearbejdning, transport og spild er behandlet. En sparet udledning er en forskel mellem to beskrevne scenarier. Rambølls analyse af 16 bygninger sammenligner tre renoveringsomfang med nybyg over 50 år. I deres beregninger lå løsningen med lavest klimapåvirkning blandt renoveringerne for alle 16. Undersøgelsens kapitel om følsomhed viser, hvorfor et nyt projekts energiforbrug og referencescenarie skal undersøges selvstændigt. [Rambøll, kap. 2–3 og 5–6](https://gi.dk/media/mgmpjbng/komparativ-analyse-af-co2udledning-og-totaloekonomi-i-renovering-og-nybyg-3-endelig.pdf)

**LCC** er en beregning af omkostninger over levetiden. Medtag fx projektering og prøver, indkøb, afmontering, opbevaring, tilpasning, montage, drift, vedligehold og udskiftning. Skriv prisår og rentesats ved sammenligning i nutidsværdi. En gratis dør kan være dyr at sætte i stand. Et dyrere, reparerbart vindue kan have lave udgifter ved næste indgreb. Hold beboernes komfort, tilgængelighed og arkitektoniske kvaliteter synlige ved siden af tallene. [Landsbyggefondens vejledning](https://totaloekonomi.lbf.dk/help/anvendelse.htm)

## Hvad kan vende valget?

- **Restlevetid.** BUILD angiver referencelevetider. Besigtigelse, eksponering, udførte reparationer og planlagt vedligehold giver grundlaget for at skønne over den bestemte dels resterende levetid. Beregn fx scenariet både med og uden en udskiftning i perioden, hvis den er usikker. [BUILDs levetidstabel](https://vbn.aau.dk/da/publications/build-levetidstabel-version-2021/)
- **Drift.** Prøv en alternativ antagelse om indetemperatur eller forbrug. I Ryesgade 30 kan både arealændringer og opdelingen mellem varme og el aflæses i kilderne. [Fem danske projekter](../cases/danske-projekter.md)
- **Udbytte og transport.** Prøv et dårligere sorteringsudbytte eller en ekstra tur til lager. Fortæl om rangordningen ændrer sig, og hvilken oplysning det da er værd at indhente. [Arbejdsarkets partifelter](../../oplaeg/forste-besigtigelse.md)

Seks danske LCAbyg-typologier giver adgang til selve beregningsmodellerne og deres forudsætninger. Brug dem til at forstå en metode. Til et konkret hus skal de virkelige materialer, mængder, isoleringsevner og restlevetider indtastes. Arkitektens materialeværktøj kan levere dokumenterede værdier for enkelte poster. Selve scenariet kræver også bygningsspecifik viden. [LCAbyg-modellerne og deres brugsbetingelser](https://lcabyg.dk/bygnings-cases/klimadata-for-renovering/) · [Materialeværktøjet](https://github.com/FremtidensTegnestue/open-source/tree/main/materialer)
