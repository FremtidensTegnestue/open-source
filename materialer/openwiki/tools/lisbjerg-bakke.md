---
type: case
title: "FBAB Lisbjerg Bakke"
description: "Originale IFC-modeller og tegninger afprøvet med dokumenterede modelmængder, eksplicit betonreferencescenarie og prioriterede datamangler."
tags: ["vandkunsten", "lisbjerg-bakke", "case", "calculations"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-d9955c06fdc484206d8845a1
    resource: repo://extracted/opensource.vandkunsten.com/07_FBABLisbjerg/index.txt
  - id: openwiki-source-0019ca133fac19d76da462b3
    resource: repo://reports/lisbjerg-bakke/data/missing-data.json
  - id: openwiki-source-e96501ce9454f0e675fd49d4
    resource: repo://reports/lisbjerg-bakke/data/summary.json
  - id: openwiki-source-f5f3731de69543a00806e211
    resource: repo://reports/lisbjerg-bakke/README.md
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# FBAB Lisbjerg Bakke

Vandkunstens casepakke indeholder originale ARK- og KON-modeller, seks tegningssæt og fotografier. Originalside: [FBAB Lisbjerg Bakke](https://opensource.vandkunsten.com/07_FBABLisbjerg/). [Original ZIP](https://opensource.vandkunsten.com/07_FBABLisbjerg/VK_FBABLisbjerg.zip) er bevaret lokalt i `archive/opensource.vandkunsten.com/07_FBABLisbjerg/`; de udpakkede filer ligger i `unpacked/archive/opensource.vandkunsten.com/07_FBABLisbjerg/VK_FBABLisbjerg/VK_FBABLisbjerg/`.

## Samlet rapport og bilag

[Rapportens indgang](../../reports/lisbjerg-bakke/README.md) linker til en 12-siders PDF, HTML, originale kildehenvisninger, en elementoversigt og en prioriteret mangelliste. Undersøgelsen er udført 17. november 2026. Den handler om, hvad det bevarede projektmateriale og den aktuelle værktøjskæde kan understøtte; den er ikke en som-udført-erklæring eller en fuld ingeniørkontrol.

## Hvad kan udtrækkes nu?

| KON-delmængde | Antal | Rapporteret volumen |
| --- | ---: | ---: |
| Ét lag `Wood - C35`, 140 mm massivtrædæk | 75 | 354,568m³ |
| `Beton In Situ - Dæk` | 20 | 209,709m³ |
| `Plywood, Sheathing` | 2 | 0,096m³ |

Materialetildelingerne er kontrolleret mod originalen. Volumenerne er BIMcrafts importerfortolkede beregninger med rapporteringstrin0,001 m³. Begge originale IFC-filer har nul eksplicitte Qto-mængdesæt. Det betyder ikke, at den originale geometri mangler. C35 dokumenterer ikke træart, densitet eller CLT-produkt, og en præcis modelmængde dokumenterer ikke faktisk leverance.

Et særskilt betonreferencescenarie bruger de 20 dæk og en manuelt valgt BR18 C25/30-X0/XC1-reference. Det giver 471.006,414 kg og 50.539,869 kg CO₂e for A1–A3 alene. Modellen dokumenterer ikke den valgte betonklasse eller referenceækvivalens. Scenariet omfatter ikke armering, andre bygningsdele eller øvrige moduler.

## Hvor er hullerne?

ARK har 2.937 kildeelementer eksklusive åbninger; 2.555 kan GUID-kobles til udtrækket. KON har 2.212 og 2.206. Disse objektantal er ikke indbyrdes adskilte materialemængder eller dækningsprocenter for byggeriet. ARK har også samlinger og børn.

Importen angiver 342 udeladelser og 145 generiske repræsentationer i ARK samt 6 udeladelser i KON. Antal kildeobjekter uden GUID-match tæller et andet forhold end importens `skipped`. Adapteren bevarer begge former for evidens. Nettovolumen for mange andre kategorier udstilles ikke gennem den undersøgte CLI-adgang; rumvolumen og åbninger indgår ikke som materiale.

Ingen fælles element-GUID’er beviser ikke fravær af fysisk overlap. Separate koordinatflytninger og fagligt mængdeansvar skal afstemmes før summering. Der dannes ingen ARK+KON-total i rapporten.

## Tegninger kan supplere materialekort

De seks PDF’er indeholder 132 sider. Alle sider er tekstudtrukket og målrettet undersøgt; fire kritiske sider er visuelt kontrolleret. Detaljer giver blandt andet lokale lagtykkelser, C18/C24-/limtræsklasser, profilgeometri og fastgørelser. De er ikke automatisk præcise produkter, EPD’er, globale mængder eller dokumentation for udført revision.

T1 har forskellige opbygninger på Snit-A og Snit-B i kassettesættet. Y2 angiver både 220 mm skelet og 240 mm isolering. Forskellene bevares som kildeoplysninger, indtil placering og revision er afklaret. Tegningskoblinger skal have PDF-side, type, sted og revisionskontekst.

## Næste arbejde

Den maskinlæsbare mangelliste har 14 prioriterede opgaver med ansvar og effekt. Start med udførte revisioner, komplet nettomængdeudtræk, ARK/KON-afstemning og dokumenterede materialekort. Produktdata, densitet, fugtgrundlag, armering og EPD/reference skal bindes til konkrete typer eller GUID’er.

Rapporten dækker også muligheder for varme, fugt, øvrige miljøindikatorer, styrke, brand, lyd, indeklima, økonomi og genbrug. Den nuværende beregnings-CLI implementerer masse, modulvis GWP-skalering og en afgrænset træfugtmetode; de øvrige områder kræver både data og implementerede, validerede faglige metoder.

## Kontrolstatus og rettigheder

Originalernes kontrolsummer er uændrede. Semantisk kildekontrol, importanalyse og beregningsafprøvning er gennemført; geometrisk fuldvalidering og dokumentation af faktisk byggeri er ikke udført. Makroer og originale Vandkunsten-programmer er ikke afviklet. Individuelle rettigheder til tegninger, modeller og fotos er fortsat ikke afklaret ved denne analyse.

[Modelberegninger](../workflows/modelberegninger.md) · [Materialedatabase](../data/materialedatabase.md) · [Rapport og reproduktion](../../reports/lisbjerg-bakke/README.md) · [Projektregister](../../catalog/projects.json)

## Offentlig læseversion

[Rapportens indgang](../../reports/lisbjerg-bakke/README.md) giver den offentlige PDF uden originalpakkens projektfoto samt de publicerede tabeller, modeludtræk og mangellister. Originale IFC-modeller, tegninger og det fulde rå parserarkiv ligger særskilt fra Git-pakken; de oprindelige adresser og kontrolsummer er bevaret. Se [arkivguiden](../../docs/ARKIV.md).
