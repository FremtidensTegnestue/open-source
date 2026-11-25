# Browserindgangen

Den offentlige side publiceres fra denne mappe med GitHub Pages. Den virker uden konto, installation, eksterne scriptbiblioteker eller en FT-server. Søgningen kører i browseren. Søgetekst og valgt materiale gemmes kun i URL-fragmentet og sendes ikke af siden som en søgeforespørgsel til en server. GitHubs hosting har egne vilkår og driftslogs.

## Data og afgrænsning

`materialer.json` er et reproducerbart, uændret udsnit af repoets Parquet-grundlag: alle 507 BR18-tabel 7-referencer fra 2025 med 2.535 observationer, kontekst og kilder. JSON-omformningen omregner ingen enhed eller værdi. Installationers 15 areal-/år-referencer holdes adskilt fra vare- og materialemængder. Datakildernes registrerede rettigheder bevares; MIT omfatter ikke automatisk dataene. Se [kilder og rettigheder](../materialer/THIRD_PARTY.md).

Browseren kan nu skalere én valgt materialereference til brugerens egen mængde. `quantityBasis` kræver overensstemmende referenceangivelser i alle fire faser og tillader kun kildens egne kg, ton, m, m², m³ eller stk. 447 referencer er understøttet; 38 R-normaliserede isoleringsreferencer, 15 areal-/år-installationsreferencer og 7 ekstra dimensionsbundne referencer afvises med forklaring. Der konverteres ikke mellem enheder. Kildedata ændres ikke, og en gemt beregning har sin egen `calculation` ved siden af de oprindelige data. Dette er ikke hele datalageret, aktuelle produktanbefalinger, en projektberegner, en komplet LCA eller en implementering af Rust-motoren i browseren. Moduler vises hver for sig. Seks betydende cifre bruges i den store talvisning, og en afrunding markeres med ≈. Kildens præcise tal og alle felter kan ses eller hentes separat. Ingen automatisk vinder udpeges.

## Vedligehold

Fra `materialer`, med Python/PyArrow installeret:

```sh
python scripts/build_browser_materials.py
python scripts/build_browser_materials.py --check
python -m unittest discover -s tests -p test_browser_materials.py -v
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
