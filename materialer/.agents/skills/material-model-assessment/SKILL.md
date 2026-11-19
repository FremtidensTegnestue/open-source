---
name: material-model-assessment
description: Hent mængder fra Solidcraft- eller BIMcraft-modeller og beregn dokumenteret vægt, modulopdelte klimabidrag eller træets fugtbevægelse med projektets materialedatabase.
---

# Materialer fra model til dokumenteret beregning

Brug `ft-materials` fra mappen `materialer`. Rust-CLI'et skriver JSON. [Installation og datamodellen](../../../docs/RUST.md) · [Afprøvet materialevalg og elementkort](../../../examples/unified-workflow/README.md)

## Arbejdsgang

- Læs `ft-materials status`. Opret den offentlige dataudgave med `ft-materials build`, hvis den endnu ikke er installeret.
- Hent geometri med `ft-materials extract MODEL --software solidcraft` eller `--software bimcraft`. Brug `--mesh-quantities` til understøttede BIMCraft-familier. Bevar modelkontrolsum, mængdeenhed og advarsler.
- Find kandidater med `search`. Kontrollér konkret produkt, observation, betingelser og kildeversion med `lookup` og `source`. Fasthold udgavens fulde ID i projektets materialevalg.
- Brug ét godkendt materialevalg for begge programmer. Revisionskortet forbinder en bestemt CAD-krop med et bestemt BIM-element og begge modellers kontrolsummer. Se eksemplets `selection.json` og `revised/transfer.json`.
- Kør `ft-materials assess MODEL --software SOFTWARE --selection VALG.json --transfer KORT.json`. Statuskode 2 angiver et delvist resultat. Vis hvilke dele der kræver afklaring.
- En ændret kilde kan kontrolleres med `check-updates`. Brug `changes FØR EFTER --selection VALG.json` til at finde berørte dele. Bevar den tidligere udgave til eksisterende projekter.

## Afgørende fortolkning

Vægt fra volumen kræver densitet; kg/m² er ikke densitet. Brug værktøjernes enhedskonvertering. Solidcrafts totale overflade er ikke et referenceareal. Arealbaseret modelberegning kræver en eksplicit `area_basis_note`.

Klimabidrag gælder den valgte kildeindikator og livscyklusmodul. En deklaration kan være pr.1000kg eller1ton. Modul D holdes særskilt; resultater er ikke automatisk en bygnings-LCA eller dokumentation for myndighedsoverholdelse. Grundlag som `1 m² with R=1 m²K/W` kræver en yderligere metode og afvises af den simple skaleringsfunktion.

Fugtbevægelse kræver en arts-/retningsspecifik koefficient, start-/slutfugt inden for kildens interval og en eksplicit antagelse om modelakse og fiberretning. Brug ikke svind grønt→ovntørt som koefficient pr. procentpoint. Brug ikke en råtræsarts koefficient som en dokumenteret CLT-egenskab.

BIMcraft0.12.0's gulvvolumener afrundes til0,001m³. Rapporten bevarer denne usikkerhed og dens bidrag til masse/klima. Præsenter ikke resultatet med større sikkerhed end kilden eller modellen understøtter.

Resultatet skal vise model, valgte data, beregninger, enheder, kildehenvisninger, antagelser og mangler. Gem CLI’ets JSON-svar i en separat rapportfil.

## Pris og budget

Læs [udviklingsgrundlag og leverandørundersøgelse](../../../docs/PRICING.md). Fælles mængder kræver ikke en bestemt placering af pris og CO₂ på skærmen. Der er ikke implementeret en generel leverandørprisforbindelse i den udgivne CLI.

Bind prisvalg til samme materialepost, fysiske mængde og gemte modelrevision, men bevar priskilde og miljøkilde hver for sig. En prisreference for en bestemt vare ændrer ikke automatisk en generisk EPD eller dokumenterer teknisk egnethed. Registrér prisdato, valuta, momsgrundlag, referenceindhold, købspakke/mindstekøb, rabat-/tilbudsbetingelser og oprindelse (eksisterende/genbrug/nyt). Brug fysiske indkøbsenheder; klimaets funktionelle R-referenceareal er ikke et købsareal.

Skeln netto, eksplicit spildtillæg og pakkeafrunding; en ubrugt pakkerest er ikke automatisk affald. Fordel ikke ordregebyrer og transport som materialefaktorer uden et valgt leveringsscenarie. Montage, prøver, bearbejdning, genbrugsundersøgelse og andre følgearbejder skal fremgå, også når de er ukendte. Ukendt pris eller mængde er ikke nul. Vis kendt delsum og dækningsmangler; antal prissatte poster er ikke procent af byggeomkostningen. Bevar en dateret reference, og adskil ændret dækning fra ændret pris/design. Kalder man resultatet LCC, kræves desuden periode, drift/vedligehold/udskiftning, rente, prisudvikling og restværdi med passende grundlag.

Budgetramme, gemt beregningsreference og forventet slutpris er forskellige. Pris og klima kan dele mængdegrundlag uden et bestemt fælles skærmlayout. Ved markedsopdatering bevares faktiske udgifter og aftalte priser efter aftalens vilkår; kun relevante ikke-aftalte restmængder genprissættes. Afstem delvis levering/fakturering mod resterende ordreforpligtelse for at undgå dobbelttælling. En tilbudspris er ikke automatisk en accepteret fast aftale.

Prioritér de priser, som gælder for den faktiske indkøbende kunde/entreprenør, med kildeidentitet, enheder, mængdetrin, leveringsbetingelser og tilladt adgang. En dokumenteret leverandørfil eller et abonnement er ikke i sig selv en offentlig API eller dagsdata. Registrér observationstid, gyldighed og seneste vellykkede kontrol særskilt. Kontrolfrekvens gør ikke kilden nyere. Hentefejl eller udløb må ikke gøre restprognosen billigere gennem bortfald af data; bevar dateret historik og vis aktuel usikkerhed. Faglige overslag og brancheindeks er andre datatyper end en konkret leverandørpris. Et universelt udløbsinterval for webobservationer må ikke kassere historiske faktiske omkostninger.

Ved undersøgelse af automatisk prisindhentning: skeln leverandørens afsendelse, modtagelse, import, projektaktivering og handel. En fakturakanal eller fakturaformat dokumenterer ikke en prisfilkanal; et PunchOut-katalog dokumenterer ikke et ubetjent pris-API. Få en virkelig eksempelfil og leverandørens felt-/adgangsbeskrivelse før en specifik parser bygges. Afstem nettopris/listepris, rabatter, begge enheder/referenceindhold, moms, kundekontekst, fuld-/ændringsfil og ophørte varer. En allerede anvendt rabat må ikke trækkes igen. En faktisk leverandørintegration må først kaldes afprøvet efter en modtaget fil eller et reelt dokumenteret svar og kontrol af anvendelsen; et planlagt testforløb eller offentligt produktløfte er ikke et bestået forsøg. DNS-/hentefejl i ét miljø er ikke bevis for manglende kundeadgang.

## Materialefelter, levetid og drift

- Brug `ft-materials fields` til definitionerne og `coverage --material ID` for at se, hvilke felter kilden dækker. Brug derefter `facts ID --field service_life_value` eller `maintenance_frequency`. Gem værdi, sammenligningstegn, enhed, del, dokumenttype og kildested i svaret.
- Læs samme felter på modellen med `ft-materials model-facts MODEL --software SOFTWARE --selection VALG.json --transfer KORT.json --field FELT`. Et materialevalg til et opslag kræver ID, modelmaterialets navn og begrundelse. Beregningsobservationer er kun nødvendige, hvis der også skal beregnes på delen.
- Hold en producents driftsinstruks, et LCA-scenarie og en generisk middellevetid adskilt. Gengiv konkurrerende kilder med deres egne betingelser og behold usikkerhed eller manglende værdier i resultatet. Modeldata og den faktiske installation har hver deres dokumentationsgrundlag.

## Reparation og adskillelse

DfD er et frivilligt tilvalg i designværktøjet. Materialer, klima, pris og budget skal fungere uden at vælge DfD. Aktivér kun et DfD-forløb efter brugerens valg for projektet eller konkrete bygningsdele; almindelige konstruktioner må ikke afvises eller automatisk få særlige DfD-beslag, prøver, følgeposter eller fremtidsgevinster. Bevaring, reparation og genbrug kan undersøges uafhængigt af et DfD-tilvalg. Bevar eksisterende DfD-prøvemodeller som valgte forsøg uden at overføre dem til nye projekters standard.

Skeln fastgørelsens tilstand fra materialets handling: et fanget beslag kan blive på bygningen og åbnes/lukkes uden at være fysisk afmonteret. Brug ikke en materialemængde som bevis for en låsetilstand. Geometriske modeller skal kontrolleres mod håndberegnet volumen og faktiske mål; en delvist afskåret boring kan ændre både mængde og funktion. CAD-legemer og fysiske produktdele kan være forskellige: behold eksplicit produktgruppering og undgå system-/del-dobbelttælling.

Ved en live CAD-gennemgang: registrér diskrete frigørelses-, udtagnings- og genmontagetilstande; kontrollér samme inventar/volumen, uændrede nabodele og slutposition mod start, også efter genåbning af den gemte fil. Umodelleret støtte, greb og værktøj skal fremgå. En parameterværdi eller visuelt fritliggende del beviser ikke fysisk håndtering, kontaktkræfter eller gentaget genbrug. Bind materialeresultater til den nye demofils kontrolsum, selv når kun placeringer er ændret; udled ikke nul påvirkning eller en klimakredit fra uændrede mængder.

Ved facadevalg behandles montering som et designvalg: dokumentér bæring/låsning, adgang/værktøj/plads, udtagningsretning, nabodele, forbrugsdele og genmontage. Undersøg lokal udskiftning såvel som samlet udtagning. En indvendig prototype dokumenterer ikke en udvendig klimaskærm, og en afmonterbar enhed beviser ikke indvendig separérbarhed. Historiske proces-/LCA-tal bliver ikke standarddata uden kontrol af enheder, reference, alder og konkret omfang. Se facadeeksemplets FACADE.md.

Når brugeren vælger DfD ved nybyggeri, udvikles adskillelighed i konstruktionsprincippet, lagdelingen og samlingerne før et senere demonteringsscenarie. Undersøg uafhængige lag, adgang/værktøj/udtagningsretning, stabilitet under indgrebet, forbrugsdele og retablering. En skrue eller et materialepas er ikke i sig selv DfD-dokumentation. Sammenlign komplette funktionelt afstemte opbygninger inkl. første opførelse; ekstra beslag og lag skal medregnes. Den nuværende CLI genererer ikke konstruktionsalternativer. Dens ens del-ID-krav må ikke omgås ved at udelade eller fejlidentificere fysisk forskellige dele.

I en kildebygget udviklingsversion: brug `ft-materials disassembly REQUEST.json` til konkrete indgrebs-/adgangsplaner, eller tilføj `--text` for en dansk læseversion. Følg [input og afgrænsning](../../../docs/DISASSEMBLY.md). Skeln adgangskrav fra følgeposter; kendt tab af en adgangsdel udløser en foreslået erstatning. Manglende mængder/kilder er åbne poster, ikke nul. D holdes særskilt, og produktreferencer er ikke fuld LCA. Brug `--check RAPPORT.json` før genbrug af gemt resultat; det kontrollerer også programhash og valgfrie model-/grundlagsfiler. Denne kommando er ikke en indbygget panelintegration og kommer ikke med den oprindeligt udgivne v0.3.0-binærfil.
