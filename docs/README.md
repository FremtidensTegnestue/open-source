# Browserindgangen

[Facadens lag](facaden.html) er en egen gemt tegningsprøve med særskilt mobilkomposition og A3-snit. [Geometri, SVG-kilder og grafiske krav](tegninger/facade/README.md) følger med. Den er ikke en live SolidCraft-kobling, beregner eller komplet vægprojektering. Prøvens mangler og åbne papir-/brugeraccept fremgår på læsesiden.

Den offentlige side publiceres fra denne mappe med GitHub Pages. Den virker uden konto, installation, eksterne scriptbiblioteker eller en FT-server. Søgningen kører i browseren. Søgetekst og valgt materiale gemmes kun i URL-fragmentet og sendes ikke af siden som en søgeforespørgsel til en server. GitHubs hosting har egne vilkår og driftslogs.

## Data og afgrænsning

`materialer.json` er et reproducerbart, uændret udsnit af repoets Parquet-grundlag: alle 507 BR18-tabel 7-referencer fra 2025 med 2.535 observationer, kontekst og kilder. JSON-omformningen omregner ingen enhed eller værdi. Installationers 15 areal-/år-referencer holdes adskilt fra vare- og materialemængder. Datakildernes registrerede rettigheder bevares; MIT omfatter ikke automatisk dataene. Se [kilder og rettigheder](../materialer/THIRD_PARTY.md).

Browseren kan nu skalere én valgt materialereference til brugerens egen mængde. `quantityBasis` kræver overensstemmende referenceangivelser i alle fire faser og tillader kun kildens egne kg, ton, m, m², m³ eller stk. 447 referencer er understøttet; 38 R-normaliserede isoleringsreferencer, 15 areal-/år-installationsreferencer og 7 ekstra dimensionsbundne referencer afvises med forklaring. Der konverteres ikke mellem enheder. Kildedata ændres ikke, og en gemt beregning har sin egen `calculation` ved siden af de oprindelige data. Dette er ikke hele datalageret, aktuelle produktanbefalinger, en projektberegner, en komplet LCA eller en implementering af Rust-motoren i browseren. Moduler vises hver for sig. Seks betydende cifre bruges i den store talvisning, og en afrunding markeres med ≈. Kildens præcise tal og alle felter kan ses eller hentes separat. Ingen automatisk vinder udpeges.

## Vedligehold

Fra `materialer`, med Python/PyArrow installeret:

```sh
python scripts/build_browser_materials.py
python scripts/build_browser_materials.py --check
python scripts/build_browser_fasteners.py --check
python -m unittest discover -s tests -p 'test_browser_*.py' -v
node --test ../docs/core.test.mjs
python scripts/build_browser_guides.py
python scripts/build_browser_guides.py --check
```

Byggeren afviser et ændret referenceomfang. En ny kildeudgave kræver bevidst afstemning af data, tekster og kontrolgrundlag. CI efterprøver den faktiske eksports værdier og kontekst, ikke blot antallet. Brug en lokal HTTP-server fra repositoryets rod til browserafprøvning, fx `python -m http.server 8765`, og åbn `/docs/`. En fil åbnet med `file://` har andre browserbegrænsninger.

Ingen testfil udføres af siden; `core.test.mjs` bruges kun ved udvikling. GitHub Pages læser HTML/CSS/JS/JSON direkte; ingen database eller motor aktiveres ved besøg.

## Læseveje uden GitHubs filvisning

Forsiden tager udgangspunkt i brugerens egen designopgave: ønsket forandring, aktuelle valg og deres konsekvenser for mennesker, arkitektoniske kvaliteter, ressourcer og klima. Den henvender sig til arkitekter, konstruktører, ingeniører, bygherrer, håndværkere og andre med en byggesag. Den beder ikke brugeren vælge fagrolle eller oprette en konto. Materialeopslag og læse-PDF'er er tilgængeligt fagligt grundlag; vinduesforklaring og det gemte regneeksempel er tydeligt valgfrie fordybelser. Ingen bestemt øvelse kræves før eget projekt. Opsætning, kode og videreudvikling har en særskilt vej.

`build_browser_guides.py` genbruger de tre SVG-tegninger og de ti kildeforbundne forklaringer i fagordbogens eksisterende vinduesark. Kun indpakning og læselayout ændres; selve tegningerne og forklaringerne bevares. Regneeksemplet læser de to gemte, uafhængige referencer i `materialer/examples/integrated-workflow/` og kopierer forsøgets faktiske modelbillede. Byggeren kontrollerer den forklarede nettogeometri, masse og enheder mod referencefilerne og afviser en gemt fejlet kontrol eller uventet struktur. `--check` sammenholder alle tre afledte filer byte for byte; CI kører kontrollen.

At generere disse læsesider gentager ikke CAD/BIM-forsøget eller en faglig eftervisning. Datoen for den gemte kontrol fremgår. Den tekniske forsøgsbeskrivelse, modellerne og originalkilderne er bevaret. Originalarkets PDF er fortsat den særskilte tegningsfil; den nye websides layout er til skærmlæsning.

## Brug direkte eller med egen AI

Forsidens `#brug-ai` viser en opgave, der kan tilpasses brugerens egen byggesag og designvalg. Den beder om kilder og skelnen mellem dokumenterede forhold, antagelser og spørgsmål til beregning eller faglig vurdering. Materialeopgaven bruger det eksisterende **Gem materialedata** for én valgt reference frem for at sende hele 4,23 MB-udtrækket til en chat. Link-/filadgang afhænger af brugerens AI; der er ikke tilføjet en chat, en ekstern AI-tjeneste eller en ny datatransmission på websiden. Den eksisterende lokale agentvej med filer, terminal og eventuelle beregningsværktøjer har særskilte forudsætninger.

Introduktionen lover ikke en ny projektvælger eller automatisk beregning af samfundsvirkning. Det eksisterende opslag, læsestof og de afgrænsede beregninger beholder deres dokumenterede omfang.

## Afprøv mængdeberegningen

Kør `node --test docs/core.test.mjs` fra repositoryets rod. Prøverne dækker de 447 understøttede referencer, fem referencebeløb tæt på 1, dansk decimalkomma, nul, negative kildeværdier, manglende værdier, referencekonflikter og afvisning af ugyldige tal, over-/underløb og særlige referencegrundlag. I browseren kontrolleres også materialeskift, nulstilling, fejlretning, tastatur, smal visning og download af både kildedata og beregning. Ingen manglende værdi må blive nul; ingen moduler summeres.

## Isoleringsvalg og materialekort

`#isolering` bruger `insulation.mjs` til 13 eksplicit afgrænsede homogene BR18-tabel 7-referencer: otte plade-/fleksible og fem løsuld-/granulatreferencer. Den tidligere enkeltmængdemetode er uændret; dette er en særskilt metode for et udvalg af de 38 R-normaliserede referencer.

Den deklarerede reference er 1 m² ved R = 1 m²K/W. Skalering pr. modul er `kildetal × areal_m2 × R_m2K_W`. Det er lineær skalering af det angivne generiske referencegrundlag, ikke en ny produkt-EPD eller en beregning af tykkelse, energiforbrug eller U-værdi. Fælles form og R er ikke teknisk ligestilling. Trykfaste, beklædte, akustik- og rørsystemer er udeladt fra dette forløb. Ingen varmeledningsevne eller densitet gættes. Areal må være nul; R skal være positiv. Ukendt forbliver ukendt, også ved nul areal. Modul D og forskellen B minus A vises fasevis; ingen total eller automatisk vinder.

Metoden kræver præcist navnematch i den gennemgåede liste, fire unikke moduler og overensstemmende referencefelter i alle fire kildeobservationer. Konflikter, ukendte profiler og numeriske over-/underløb afvises. `compareInsulation` muterer ikke kildereferencerne. Ugyldige eller tomme input fjerner tidligere resultater og download. Gem sammenligning inkluderer input, metodeversion, udgavens Parquet-manifesthash og begge uændrede kildepakker. Gamle downloads genberegnes ikke automatisk. Beregningen foregår lokalt i JavaScript; Rust-motorens beregningskontrakt er ikke udvidet.

Kontroleksempel: 20 m² ved R5 giver 100 referenceenheder. D1535 giver A1–A3 = 59,015 og C4 = 1,804 kg CO₂e. D1627 giver A1–A3 = −214,2 og C3 = 322,3 kg CO₂e. De negative produktionstal er ikke et samlet negativt livscyklusresultat. Testene efterprøver alle fire moduler og forskelle, uafhængig areal-/R-skalering, samme valg, nul, manglende data og ændret referencegrundlag. Før ændring af listen skal den konkrete references funktion og skalerbarhed gennemgås; undlad at tilføje alle R-referencer via et navnefilter.

Kilder til enhedsgrundlaget: [BR18 tabel 7](https://www.bygningsreglementet.dk/Bilag/B2/Bilag_2/Tabel_7) og [officiel vejledning, afsnit 1.5](https://www.bygningsreglementet.dk/tekniske-bestemmelser/11/brv/bygningers-klimapaavirkning-1-juli-2025/kap-1_5/). JSON-filen og alle oprindelige kildetal er uændrede.

`#materialevalg` viser korte, redaktionelle kort om biobaseret isolering, ålegræs til akustik, en konkret linoliemalings-EPD og bevaring. [BUILD 2026:25](https://vbn.aau.dk/da/publications/innovationsbehov-for-biobaseret-byggeri/) begrunder de dokumentationsspørgsmål, der skal afklares; rapporten er ikke en produktgodkendelse. [MD-23213-EN_rev2](https://www.epddanmark.dk/media/ncmh1zig/md-23213-en_rev2.pdf) omfatter én liter udendørs maling i én farve; den linkes som original og bruges ikke som generisk beregningsfaktor. Kildernes fulde PDF'er eller nye EPD-tal redistribueres ikke.

`#nyt` adskiller ændring af visning/metode fra dataudgave og tilbyder kontakt samt den eksisterende GitHub-hjælpeformular. Nye kilder skal kontrolleres for repræsentativitet, moduler, udgave og viderebrugsret før publicering. Der er ikke tilføjet en API, en server, en kontaktformular med datalagring eller en automatisk opdateringstjeneste.

## Skruer, beslag og tætning

`#fastgoerelser` er et særskilt forløb. `fastgoerelser.json` bevarer to originale generiske ÖKOBAUDAT-referencer, ni GWP-total-observationer og to kilder fra Parquet. BR18-udtrækket med 507 referencer er uændret. Byggeren `build_browser_fasteners.py` kan genbygge filen og med `--check` sammenholde alle bytes; kilde- og referencemetadata kontrolleres før eksport. Se [gennemgåede kilder og udgaver](../materialer/docs/sources/fastgoerelser-og-taetning.md).

`fasteners.mjs` understøtter kun de to gennemgåede ID/navne i udgave 20.26.070, 1 kg reference, tysk geografi og EN 15804+A2 (EF 3.1). Den konkrete LCIA-indikator-UUID skal være GWP-total, ikke GWP-fossil. Mængden er skruernes nettovægt i kg. Ingen omregning fra stykantal, bæreevne-/korrosionsvurdering, automatisk vinder eller summering med BR18. `oekobaudat_screw_mass.v1` skalerer hver oplyst fase; de tre manglende faseværdier indsættes ikke i kildedata. Visningen viser C4 som ukendt for begge og C3 som ukendt for rustfri, også ved 0 kg. D holdes særskilt. C2's kildescenarie på 50 km transport efter brug er bevaret. A4/A5/B er ikke tilføjet.

Skruefilen indlæses uafhængigt af BR18-filen. Fejl afviser beregningen, rydder resultat og download og giver genforsøg; der bruges ingen tavs reservekilde. Valgskift og vægtændring beregner på ny; tomme/ugyldige værdier fjerner det gamle resultat. Download indeholder input, metode, præcise resultater og den valgte uændrede kildepakke. Dette er fortsat lokal JavaScript, ikke en aktivering eller udvidelse af Rust-motoren.

Kildekortene for BSIN/Connectors, TESCON VANA og INTELLO linker til producenternes originaler. De indeholder ingen importerede EPD-faktorer eller genudgivne PDF'er. De tre poster tælles ikke som færdige beregningsmaterialer. Teksterne adskiller referenceenhed, produktvariant, gruppe-/produktkilde, emballage og åbne system-/rettighedsforhold. Vær varsom med ændrede producentlinks: det læste dokuments SHA-256 og version fremgår af kildenotatet; et live-link kan senere pege på en ny udgave.
