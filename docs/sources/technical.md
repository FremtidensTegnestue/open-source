# Fysiske, termiske, optiske og fugttekniske materialedata

Dette datasæt er indsamlet fra de originale OpenStudio- og EnergyPlus-repositorier. Der er gemt **15 komplette originalfiler**, **3.183 kildebestemte materialeposter** med **1.374 forskellige navne** og **15.127 numeriske observationer**. Materialeposter er poster i de tekniske biblioteker; de er ikke 3.183 dokumenterede danske handelsprodukter eller entydige kemiske materialer.

## Originale kilder

- [OpenStudio standards, commit 0bd835164403285d82654c422e525a9877e3c47e](https://github.com/NatLabRockies/openstudio-standards/tree/0bd835164403285d82654c422e525a9877e3c47e): alle fem materialebiblioteker i denne version, `ashrae_90_1`, `ashrae_90_1_prm`, `cbes`, `deer` og `necb/NECB2011`.
- [EnergyPlus, commit fcdda275c87255660bcad034197c03b64af2b0a8](https://github.com/NatLabRockies/EnergyPlus/tree/fcdda275c87255660bcad034197c03b64af2b0a8/datasets): hele `ASHRAE_2005_HOF_Materials.idf`, `MoistureMaterials.idf`, `WindowBlindMaterials.idf`, `WindowGasMaterials.idf`, `WindowGlassMaterials.idf`, `WindowScreenMaterials.idf` og `WindowShadeMaterials.idf`.
- OpenStudios originale `Standards.Model.rb` er gemt som kilde til de anvendte enheder. Koden er læst som dokumentation; den udføres ikke.
- Begge repositoriers originale licensfiler er gemt. Begge bruger særlige permissive licenser med betingelser for ophavsangivelser og brug af navn; de må ikke blot ommærkes til en fælles MIT- eller standard-BSD-licens. EnergyPlus-datasæt har også henvisninger til ASHRAE Handbook 2005 og andre oprindelige ophav. Dette er en registrering af de fundne vilkår, ikke en fuld rettighedsvurdering af hver citeret håndbogsværdi.

Hver fil er bevaret uden ændring under `data/raw/technical/<kilde>/<original sti>`. Originale URL'er, hentetid, SHA-256, licensobservation og lokal sti er i `data/staging/technical/sources.jsonl`. De oprindelige NREL-adresser viderestiller nu til NatLabRockies; de fastlåste commit-adresser gør snapshot-identiteten entydig.

## Dækning

De numeriske observationer omfatter blandt andet:

- Tykkelse, densitet, specifik varmekapacitet, varmeledningsevne og termisk modstand.
- Termisk, sol- og synlig absorptans.
- Glaslags transmittans, reflektans, emissivitet og optiske egenskaber for for- og bagside.
- Tekniske parametre for solafskærmning, persienner og skærme.
- 191 fugtrelaterede observationer fra EnergyPlus: dampdiffusionsmodstand, fugtmodelkoefficienter, penetrationsdybder, porøsitet, sorptionskurver, kapillære transportkurver samt fugtafhængig varmeledningsevne.

Datasættet indeholder 77 forskellige egenskabsfelter efter normalisering. Dette er ikke et løfte om, at alle egenskaber findes for hvert materiale. Fugtkurverne repræsenteres af 107 y-observationer med parrede x-værdier, enheder, punktindeks og kildelinjer i `conditions.curve_point`; x-aksens punkter tælles ikke som selvstændige observationer.

Materialefamilierne er opdagelsesgrupper baseret på navne og kildekategorier: beton/mørtel, murværk, metaller, glas, isolering, træ, polymerer og øvrige. Denne automatiske gruppering dokumenterer ikke teknisk ækvivalens mellem poster.

## Enheder og fortolkning

**OpenStudio-data gemmes i deres originale imperiale enheder.** Ingen SI-omregning er udført i denne indsamling. `Standards.Model.rb` dokumenterer blandt andet `in` for tykkelse, `lb/ft^3` for densitet, `Btu/lb*R` for specifik varmekapacitet og `Btu*in/hr*ft^2*R` for varmeledningsevne. JSONL-felterne bruger en entydigere matematisk skrivemåde med `degF` for temperaturdifferencen, men værdierne er uændrede. Referencen til den originale enhedskode gemmes i hver observations `conditions`.

Fire AirGap-posters modstand er mærket `source_ambiguous`: det originale Ruby-forbrug angiver en usædvanlig omregning med pr. tomme og `m*K/W`. Vi påtvinger ikke disse værdier den konventionelle arealmodstandsenhed. De skal undersøges, før de anvendes i beregninger.

**EnergyPlus-data beholder deres feltangivne enheder.** Felter uden en kildeangivet enhed er kun mærket dimensionsløse, når feltets betydning entydigt er en andel, reflektans eller tilsvarende. Øvrige uklare enheder markeres `source_unspecified` og må ikke automatisk antages at være SI.

Fugtkurver og EMPD-/HAMT-parametre er inputs til bestemte EnergyPlus-modeller. De er ikke direkte mål for træets svind, og de skal bruges sammen med øvrige felter fra samme objekt og den tilsvarende modelbeskrivelse. Den oprindelige objekttype, feltnavn, rækkefølge og kildelinje bevares i `conditions` og `source_locator`.

## Parsning og dubletter

- Alle fem OpenStudio-bibliotekers 5.351 inputposter læses. 2.542 fuldstændigt identiske poster deduplikeres. De øvrige 2.809 fuldstændige poster bevares hver for sig, også når navne ligner hinanden. Forskelle i metadata eller egenskaber bevares; identiske navne er ikke tilstrækkeligt til at sammenlægge materialer.
- Andre forekomster af en identisk post gemmes som yderligere kildehenvisninger i observationskonteksten.
- NECB-JSON bruger `tables.materials.table`, mens de øvrige bruger `materials`. Kildehenvisningerne bevarer den faktiske JSON-sti.
- EnergyPlus læses som IDF-data. Kun `Material*`- og `WindowMaterial*`-objekter importeres. Konstruktioner og styringsobjekter optræder ikke som materialeegenskaber.
- EnergyPlus-materialeegenskabsobjekter med samme materialereference i samme fil samles i én materialepost. Hvert datapunkt beholder sin konkrete objekttype og position, så sorptions- og transportkurver ikke mister forbindelsen til deres model.
- Strukturfelter som antal kurvepunkter tælles ikke som materialeegenskaber.
- 685 numeriske OpenStudio-felter importeres ikke som selvstændige observationer: 582 `cavity_insulation`, 94 `solar_diffusing` og 9 `frame_width`. Deres betydning/enhed er ikke tilstrækkeligt dokumenteret i den gemte forbrugskode; værdierne er bevaret i originalfiler og `not_imported.json`.
- Nuller, tomme felter og manglende værdier bliver ikke opfundet som nul. Faktisk rapporterede nulværdier bevares.

## Genkørsel

Fra repository-roden:

```sh
python3 collectors/technical.py
```

Kommandoen genbruger bevarede originalfiler og genskaber JSONL-filerne. `--refresh` henter de samme fastlåste commit-versioner igen. Indsamlingen kræver Python-standardbiblioteket og en netforbindelse ved første hentning. Upstream-kode udføres ikke.

De normaliserede filer er `materials.jsonl`, `observations.jsonl`, `sources.jsonl` og `summary.json` under `data/staging/technical/`. Felter om kilde, enhed og kontekst skal bevares ved import til den fælles database.

## Kontrol og begrænsninger

Collectorens kontrol omfatter unikke ID'er, komplette materialereferencer og kildereferencer, endelige numeriske værdier og genberegning af alle originalfilers SHA-256. Derudover er observationer kontrolleret mod de direkte kildelinjer eller JSON-felter.

De importerede værdier er først og fremmest simuleringsbiblioteksdata. De er ikke automatisk aktuelle produktdeklarationer, danske dimensioneringsværdier eller egnede til konstruktions-, brand- eller myndighedsdokumentation. Der er ikke gennemført et forsøg eller en faglig certificering af værdierne. Dubletter og uenigheder mellem uafhængige kilder er ikke automatisk fjernet.
