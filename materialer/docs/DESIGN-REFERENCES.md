# Inspirationskilder til det SolidCraft-baserede designværktøj

## Aktuel prioritering efter kodegennemgang, 20. november 2026

Læs [gennemgangen med reproducerede fund og acceptkrav](REVIEW-2026-11-20.md) før videre implementering. Brugerkravene er fortsat SolidCraft, enkle materialevalg med synlige projektfølger, arkitektonisk frihed, nybyggeri/renovering/transformation og DfD som tilvalg. Prisformålet er et internt overslag og ensartet tilbudsgrundlag til flere leverandører, ikke automatisk prisfastsættelse.

Vores anbefaling er én lille, sammenhængende prøve: revisionsbundet del → to funktionelt afstemte materialeopbygninger → klima og prisoverslag inklusive følgeposter → behold/fortryd/genåbn → fælles tilbudsliste. Fast delidentitet, ændringshåndtering og tilbuddenes anvendelsesvilkår skal afklares i dette forløb. En faktisk brugerprøve skal vise forståelse og korrekt opgaveløsning. Fuld indkøbs-/fakturastyring, lagerintegrationer og flere fagmotorer kommer senere efter behov. Det er prioritering, ikke ny implementering eller bestået integration. De følgende afsnit bevarer de historiske undersøgelser.

Kilder læst 19. november 2026; opsamling afsluttet 20. november 2026. Dette er læsning af offentlige primærkilder, ikke praktiske tests, integrationsvalg eller overtagelse af andres metoder/data. Den tidligere [1to10-prøve](1TO10.md) er særskilt.

| Reference | Dokumenteret beskrivelse | Vores forslag til læring |
| --- | --- | --- |
| [2050 Materials](https://docs.2050-materials.com/methodology-documentation/tools/embodied-carbon-optimiser-tools) | Tidlige opbygningsalternativer med A1–A3-bidrag. | Undersøg lag- og systemskift med komplette følgeposter. |
| [Ubakus](https://www.ubakus.de/en/r-value-calculator/) | Lag, stolper/spær og visninger for varme/fugt. | Forklar faglige følger af et materialeskift med synligt metodeomfang. |
| [dataholz](https://www.dataholz.eu/en/components/information-about-components.htm) | Opbygninger med lag og dokumenterede egenskaber; miljødelen A1–A3. | Bind konkrete varianter til deres anvendelsesområde og kildegrundlag. |
| [EC3](https://docs.buildingtransparency.org/ec3/main-features/find-and-compare-materials) | EPD-søgning efter egenskaber/lokation med statistik og usikkerhed. | Vis hvorfor alternativer er sammenlignelige og hvor datadækningen ændres. |
| [Rotor DC](https://rotordc.com/) | Varer, fotos og beskrivelser samt demontering/bearbejdning/salg. | Et konkret fund kan påvirke arkitekturen; registrér parti, stand og faktisk oprindelse. |
| [Madaster](https://docs.madaster.com/us/en/platform-pages/building/circularity.html) | Materialestrømme, lag, cirkularitetsmetode og ukendte elementer. | Bevar materialehistorik og synlige datahuller uden automatisk grøn score. |
| [Qflow](https://www.qualisflow.com/invoice-reconciliation-finance) | Sammenhold af ordre, faktisk levering og faktura. | Afstem projekteret, bestilt, leveret og indbygget med pris/klima. |
| [Speckle](https://speckle.systems/present-and-review-models/) | Modelversionssammenligning ned til objekter. | Forklar hvilke ændringer der påvirkede regnskabet, med stabil identitet. |

## Kritiske afgrænsninger

- [2050 Materials' fallbackværdier](https://docs.2050-materials.com/methodology-documentation/fallback-values) er estimater af manglende fysiske/tekniske egenskaber. Estimeret, generisk, dokumenteret og ukendt er forskellige datatilstande. Ingen stille erstatning af mangler med skøn i vores motor.
- [EC3's sammenligningsmetode](https://docs.buildingtransparency.org/methodology/epd-comparability) fokuserer på A1–A3, med angivet A5/B1-undtagelse for isolering/blæsemidler. Tværgående livscyklusvalg kræver udskiftning og slutbehandling. Usikkerhedsintervaller skal have en metode, ikke en opdigtet standardprocent.
- dataholz' grundtegning kan være fælles for flere varianter. Afstem tegning, lag og egenskaber; [national anvendelse og projektspecifik kontrol](https://www.dataholz.eu/en/terms-of-use-for-germany.htm) består. Kataloget er ikke automatisk dansk myndighedsdokumentation. Samlingsafsnittet var angivet under revision på den læste forside.
- [Ubakus' fugtmetode](https://www.ubakus.de/berechnung-des-feuchteschutzes/) beskriver både 1D og et 2D-forløb. Ældre brugerkommentarer dokumenterer ikke hele den aktuelle metode. Vis metodegrænser frem for universel fugt-/ventilationsgodkendelse.
- Den læste [Rotor DC-gulvvare](https://rotordc.com/shop/999flo183-m2-solid-oak-parquet-with-singularities-w-19-cm-sold-per-m2-63356) beskrives som ny og aldrig monteret. Butikstype bestemmer ikke oprindelse. Prisen/varianten i webudtrækket var tvetydig; ingen pris er importeret, og lager/API/reservation er ikke bekræftet. Et vindueslink fra forsiden gav 404.
- Qflow beskriver også menneskelig verifikation. Et foto/AI-udtræk er ikke alene produktmatch, dubletkontrol eller bevis for indbygning. En levering og en faktura er forskellige registreringer.
- Speckles generelle modelkoblinger dokumenterer ikke SolidCraft-understøttelse. Ingen connector eller ny cloudarkitektur vælges på dette grundlag.

## Prioriteret forslag til en senere acceptprøve

Start med 2050 Materials, Ubakus og dataholz som tre komplementære referencer for samme materialeopgave; brug EC3 som metodekontrol. Rangordenen er vores faglige vurdering, ikke en målt produkttest.

I SolidCraft: vælg én væg → åbn lag → prøv isolering/beklædning → vis afledte mængder/følgeposter → vis klima/pris ekskl. moms/arbejde for del og projekt → behold eller fortryd → genåbn. Sammenlign samme funktion og datadækning. Mål opgaveløsning og forståelse, ikke kun antal klik. Dette er et forslag, ikke udført eller bestilt integration.

Arkitektonisk frihed, nybyggeri/renovering/transformation og DfD som frivilligt tilvalg består. Ingen skjult samlet score eller automatisk arkitektonisk fravalg. Ingen praktisk test af de otte apps, konto, modelupload, handel, API-adgang eller overtagelse af bibliotek er udført i denne runde.


## Fra design til leveranceoverblik — udviklingsforslag 20. november 2026

Et samlet overblik foreslås knyttet til de samme bygningsdele, revisioner og fysiske mængder som klima og pris. Leverancer omfatter produkter, arbejde og information. En bygningsdel kan modtage flere leverancer; én leverance kan betjene flere dele. Registrér konkret omfang, ansvarlig, modtager, forudsætninger, dato og accept. Hold geometrisk færdig, produktvalgt, bestilt, leveret, monteret og kontrolleret adskilt; del-levering afslutter ikke automatisk resten.

Følg projekteret, reserveret, bestilt, leveret, indbygget, restlager, retur og spild. Afstem økonomiens overslag, aftalte køb, faktisk/faktureret/betalt og restprognose uden at overskrive budgetrammen. En faktura beviser ikke montage; en følgeseddel beviser ikke indbygning. Substitution kræver synlige følger for egnethed, mængder, montage, tid, pris og klima. Bekræftede aftaler må ikke omskrives stiltiende ved en modelrevision.

Tre mulige indgange til samme grundlag: bygningen, leverancerne og konsekvenserne. Vis fase-/opgaverelevante oplysninger og næste handling, ansvarlig og frist; resten kan åbnes. Arkitektonisk frihed og DfD som frivilligt tilvalg består. Dette er produktudvikling, ikke implementeret ERP, byggeledelse, indkøbsret eller myndighedsgodkendelse.

Metodeinspiration: [UK BIM Framework, Guidance Part A, edition 2, februar 2021](https://www.ukbimframework.org/wp-content/uploads/2021/02/Guidance-Part-A_The-information-management-function-and-resources_Edition-2.pdf), udvalgte afsnit om ansvar, informationsbehov og accept; [GS1s byggeside](https://gs1.eu/activities/construction/) om sporbar identitet. Ingen læsning af ISO-standardfuldtekst eller bekræftet fælles leverandør-API udledes heraf.

Foreslået acceptprøve: én vindues-/facadeleverance fra valgt del til dellevering, montage og dokumentation, med en substitution og synlige klima-/pris-/tidsfølger. Ingen faktiske ordrer og ingen ny funktion er oprettet med dette forslag.


## Undersøgelse af leveranceforløbet — 20. november 2026

Kodelæsning og seks isolerede, fiktive budgetprøver viser, at den eksisterende prisdel understøtter faste ordre-/fakturanettosnapshots, men ikke modtagelse, skade, karantæne, montage, retur-/kreditforløb eller slutaccept. Metadata om fysisk levering ændrer ikke økonomiberegningen og må ikke omtales som implementeret leverancestyring. Et ændret nettotal beviser ikke bevaret hændelseshistorik.

SolidCraft-udtrækket danner aktuelt identitet af legemenavnet (`solidcraft:{name}`); det er ikke eftervist som stabilt gennem omdøbning, kopiering og opsplitning. Det er ikke bevis for, at SolidCraft mangler andre identifikatorer. Anbefalet afgrænset næste prøve bruger faste logiske del-ID'er med revisionsbundet modelkobling og eksplicit afstemning ved tvivl. Bind ikke gamle ordrer/garantier til nye dele alene ved navne- eller geometrilighed.

[UK BIM Framework Guidance F, edition 1, september 2020](https://ukbimframework.org/wp-content/uploads/2020/09/Guidance-Part-F_About-information-delivery-planning_Edition-1.pdf), udvalgte afsnit 3.4/4.4/4.5, beskriver informationsleverancer med ansvar, afhængighed, omfang og milepæle. Informationsplanen er ikke i sig selv en fysisk logistikplan. [Dalux Handover-guiden](https://support.dalux.com/hc/en-us/articles/9998743362588-How-to-fill-out-Assets-in-Handover) viser produkter, placering, dokumenter og review; dens ét-produkt-pr.asset må ikke ukritisk bruges til en flerlaget væg. [GS1s identifikatorer](https://www.gs1.dk/om-gs1/overblik-over-gs1-standarder) beskriver produkt, lokation og forsendelse, men bekræfter ikke stand, reservation eller en tilgængelig leverandør-API. Ingen af disse eksterne systemer er praktisk selvafprøvet i undersøgelsen.

Anbefaling: afprøv én leverance med delvis modtagelse, skade, eksplicit accepteret substitution og bilag. Hold designvalg, aftalt indkøb, fysiske hændelser, dokumentreview og økonomi særskilt. Vis næste relevante handling med ansvarlig og frist; tillad uafklarede oplysninger under skitsering. Genbrug eksisterende beregningskerner og begynd med et lille lokalt prøvegrundlag. Ingen ny database, cloudarkitektur, CADflade eller leverandørintegration er valgt eller bygget med denne research.


## Parathed til publicering og næste prøve — review 20. november 2026

Researchen kan publiceres med sine afgrænsninger. [Gentag de seks fiktive budgetgrænseprøver](../examples/pricing/README.md#gentag-den-afgrænsede-leveranceundersøgelse) med scriptet i repoet. Tidligere fandtes kun et lokalt projektscript; den fælles udgave har relative stier, skriver kun til terminalen og ændrer ingen projektdata. Beståede budgetprøver dokumenterer ikke en leverancemotor eller praktisk SolidCraftbetjening.

Før implementering skal disse åbne forhold prøves på en lille opgave:

- Fast delidentitet gennem omdøbning, kopi/split, genåbning og projektkopi; korrekt fordeling af fælles indkøb på flere dele uden mængde-/klimadubletter.
- Ændret model under redigering, sene svar, genimport af samme dokument og samtidige redigeringer. Eksisterende filbindinger er ikke en færdig flerbrugerløsning.
- Aftalehistorik for substitution, retur, annullering og kredit, uafhængigt af modtagelse, montage og dokumentaccept.
- Ejerskab, kundeadskillelse og faktisk brugs-/videreformidlingsret til kataloger/priser/bilag; læsbar eksport og afprøvet gendannelse.
- Faglige følger af ændret produkt og en praktisk brugerprøve med fase-/opgaverelevante oplysninger.

Prioriteringen præciseres: begynd med én del i forløbet modelvalg → materialevariant → aktuelt klima/pris → fortryd → gem/genåbn. Kobl derefter én afgrænset leverance til det samme grundlag. Det tidligere fulde leverancescenarie er en senere kravprøve. Dette er en anbefaling, ikke ny bestilt integration, cloudarkitektur eller et fuldt byggeledelsessystem. Arkitektonisk frihed og DfD som frivilligt tilvalg består.
