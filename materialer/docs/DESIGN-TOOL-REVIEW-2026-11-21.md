# Gennemgang af designværktøjet · 21. november 2026

Målet er let og overskuelig undersøgelse af materialevalg, klima og økonomi under design. Dette er en kilde-/funktionsgennemgang og afprøvning af den afgrænsede SolidCraft-facade. Selvstændig nybrugerbetjening er endnu ikke dokumenteret.

## Forbedringer i den fungerende facade

Den lokale ledsagende visning har tre indgange: **Overblik**, **Sammenlign** og **Mål og grundlag**. Overblik viser kendt materialedelsum, bidrag pr. m², prisstatus og højst tre næste handlinger. Kilder, mængder og øvrige mangler kan foldes ud. SolidCraft bevarer modelredigering og native fortrydelse.

Budgetmål og mål for den viste klimadelsum kan gemmes. Ukendt prisprognose giver ingen påstand om overholdt budget. Antal prissatte poster er ikke økonomisk dækningsgrad. Ændret areal vises ved sammenligning; en mindre opgave er ikke automatisk et bedre materiale.

Betragtningsperiode og kilde-/antagelsesbundet levetid pr. post giver mulige udskiftningsår, uden automatisk udskiftning ved slutøjeblikket. Dette beregner endnu ikke udskiftningernes klima, arbejde eller følgeposter. Det er en scenariefunktion, ikke en fuld livscyklusvurdering eller garanti.

Grundlaget samler arkitektur/brug/adgang; sted/terræn/fundering; produkter; transport/spild; levetid; energi/indeklima; bæring; brand; fugt/tæthed; lyd; ventilation; dagslys; installationer; bevaring/genbrug; indkøb/leverancer og drift/aflevering. DfD er et frivilligt ekstra område. Ét område redigeres ad gangen med status og reference. **Grundlag registreret er ikke teknisk eftervist.** Ingen af disse notater skaber automatisk en fagberegning eller grøn score.

Mål og grundlag ligger separat fra målte mængder og kildeberegning. Skift af post i formularen er visningskontekst; det skal ikke genberegne klimatallet eller gøre blanke felter til input. Gemning er revisionsbundet, og eksterne filændringer må ikke overskrives ubemærket.

## Prioriterede næste forbedringer

1. **Indtastning på rette sted.** Egne pris-/arbejdsinput skal kunne redigeres direkte fra regnskabsvisningen med læsbare enheder, kilde og dato samt afprøvet native fortrydelse/genåbning. Nu indtastes de stadig i SolidCrafts Parameters; dette er en reel resterende friktion.
2. **Hele opbygninger.** Alternativer skal medtage underlag, isolering, membraner, fastgørelser, tape, fuger, behandling og nødvendigt følgearbejde. Brugeren vælger et alternativ med samme dokumenterede funktion, ikke kun et materialeikon. Den åbne facadeprøve er ikke automatisk en komplet ydervæg.
3. **Livscyklus med fælles omfang.** Kobl transport, spild, vedligehold og udskiftning til kilde-/motorfunktionerne. Følg adgang, tab, retablering og affald. Antal udskiftninger alene giver ikke B4. D vises særskilt; ukendte moduler er ikke nul.
4. **Eksisterende byggeri.** Prøv samme sammenhængende forløb på en registreret bygningsdel med bevar/reparér/udskift. Oprindelse, stand, restlevetid og klargøring skal følge scenariet. Genbrug er ikke automatisk nulbelastning eller fremtidig kredit.
5. **Selvstændig brug.** Afprøv ren installation og en konkret opgave hos tre nye brugere: åbn, skift, forklar forskellen, find en mangel, fortryd, gem og genåbn. Observer fejl og hjælpebehov; antal knapper beviser ikke intuitiv brug.

## Parametre skal have en funktion

| Område | Nødvendigt grundlag | Aktuel facadefunktion |
|---|---|---|
| Mængder/materialer | Geometri, logisk del-ID, enhed, tværsnit/tykkelse, produkt/kilde | Beregnes i afgrænsede grupper; generiske proxyer er synlige |
| Klima | Mængde/referenceenhed, kilde og version, moduldækning | Kendt A1–A3+C3+C4, D særskilt; øvrige moduler åbne |
| Økonomi/arbejde | Nettomængde/købspakke, prisgrundlag/dato, timer/sats, levering | Interne overslag og ukendte værdier; ingen aktiv leverandørforbindelse |
| Levetid | Periode, levetid/restlevetid, kilde, adgang og indgreb | Udskiftningsår beregnes; hændelsers klima/arbejde mangler |
| Transport/spild | Afstand, last/parti, transportmiddel, leverancer, afskær/affald | Grundlagsområde; endnu ikke koblet til facadens klimatal |
| Bevaring/genbrug | Stand, oprindelse, reparation, restlevetid, faktisk videre brug | Grundlagsområde; ingen automatisk genbrugskredit |
| Tekniske egenskaber | Krav, anvendelse, konkret samlet opbygning og samlinger | Notater/afklaringer; ingen facadefaglig godkendelse |
| Drift/aflevering | Brug, adgang, vedligehold, ansvar og dokumentation | Grundlagsområde; ikke driftsovervågning eller leveranceaccept |

Registrér kun yderligere felter, når de understøtter en konkret beslutning, beregning eller afklaring. Arkitekturens kvaliteter skal kunne fastholdes, mens relevante alternativer undersøges. Undgå en skjult samlet score eller en automatisk vinder på ufuldstændige data.

## Kontrol og grænser

18 facade-/grundlagstests og 42 pristests er afprøvet. En faktisk native målændring, fortrydelse, UI-gemning, scenarielagring/genåbning samt revisions- og inputafvisning er kontrolleret lokalt. Det er ikke ekstern brugeraccept eller et generelt CAD-plugin.

De tre tidligere dokumenterede generelle tilbuds-/ordrebegrænsninger består; facadeadapteren modtager kun interne skøn. Fuld LCA, flere opbygninger, tekniske eftervisninger, generel elementvælger, kombinationssøgning, native panel og leverandørfeeds er fortsat åbne udviklingsområder. Se [facadevejledningen](../examples/facade/README.md) og [det tidligere review](REVIEW-2026-11-20.md).
