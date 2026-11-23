# Browserindgangen

Den offentlige side publiceres fra denne mappe med GitHub Pages. Den virker uden konto, installation, eksterne scriptbiblioteker eller en FT-server. Søgningen kører i browseren. Søgetekst og valgt materiale gemmes kun i URL-fragmentet og sendes ikke af siden som en søgeforespørgsel til en server. GitHubs hosting har egne vilkår og driftslogs.

## Data og afgrænsning

`materialer.json` er et reproducerbart, uændret udsnit af repoets Parquet-grundlag: alle 507 BR18-tabel 7-referencer fra 2025 med 2.535 observationer, kontekst og kilder. JSON-omformningen omregner ingen enhed eller værdi. Installationers 15 areal-/år-referencer holdes adskilt fra vare- og materialemængder. Datakildernes registrerede rettigheder bevares; MIT omfatter ikke automatisk dataene. Se [kilder og rettigheder](../materialer/THIRD_PARTY.md).

Dette er første browseropslag, ikke hele datalageret, aktuelle produktanbefalinger, en projektberegner, en komplet LCA eller en implementering af Rust-motoren i browseren. Moduler vises hver for sig. Seks betydende cifre bruges i den store talvisning, og en afrunding markeres med ≈. Kildens præcise tal og alle felter kan ses eller hentes separat. Ingen automatisk vinder udpeges.

## Vedligehold

Fra `materialer`, med Python/PyArrow installeret:

```sh
python scripts/build_browser_materials.py
python scripts/build_browser_materials.py --check
python -m unittest discover -s tests -p test_browser_materials.py -v
node --test ../docs/core.test.mjs
```

Byggeren afviser et ændret referenceomfang. En ny kildeudgave kræver bevidst afstemning af data, tekster og kontrolgrundlag. CI efterprøver den faktiske eksports værdier og kontekst, ikke blot antallet. Brug en lokal HTTP-server fra repositoryets rod til browserafprøvning, fx `python -m http.server 8765`, og åbn `/docs/`. En fil åbnet med `file://` har andre browserbegrænsninger.

Ingen testfil udføres af siden; `core.test.mjs` bruges kun ved udvikling. GitHub Pages læser HTML/CSS/JS/JSON direkte; ingen database eller motor aktiveres ved besøg.
