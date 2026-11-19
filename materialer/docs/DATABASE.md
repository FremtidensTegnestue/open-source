# Materialedatabase: struktur og anvendelse

Den aktive CLI er skrevet i Rust. Kør `ft-materials build` for at oprette den delte base og den første udgave. Siden her beskriver også v0.1-arkivet. [Læs om den aktuelle datamodel](RUST.md)

## Fra en ny download af projektet

Det komplette strukturerede datasæt følger med i `data/parquet/`. Gendan arbejdsdatabasen før de øvrige eksempler:

```sh
python -m pip install -r requirements.txt
python scripts/build_database.py
python materials.py verify --database-only
```

Dette bruger alle medfølgende data og kræver ikke, at råkilder eller stagingfiler først indsamles. Se [den offentlige dataguide](../data/README.md) for formater, kontroller og den alternative færdige SQLite-download. `materials.py build` længere nede på siden er den avancerede arbejdsgang til en ny indsamling; `materials.py verify` uden tilvalg kontrollerer også de særskilte originalfiler.

Databasen ligger i `data/materials.sqlite`. SQLite kan åbnes fra Python, Rust og almindelige SQLite-programmer. Det medfølgende CLI er `python3 materials.py`; alle svar er JSON. Database og CLI er bygget i denne opgave. Der er også implementeret en kildebaseret beregningsmotor og read-only modeladaptere til Solidcraft/BIMcraft; se [beregningsguiden](CALCULATIONS.md).

## Mapper

| Placering | Indhold |
| --- | --- |
| `data/raw/<datasæt>/` | Originale downloadede PDF-, JSON-, Excel- og øvrige kildefiler |
| `data/staging/<datasæt>/sources.jsonl` | Kilderegister med URL, rettigheder, filsti og SHA-256 |
| `data/staging/<datasæt>/materials.jsonl` | Kildebestemte materiale-, produkt- og referenceposter |
| `data/staging/<datasæt>/observations.jsonl` | En observation pr. egenskab, modul og betingelsessæt |
| `data/staging/<datasæt>/summary.json` | Dækning, antal, indsamlingsfejl og begrænsninger |
| `collectors/` | Scripts til at hente og udtrække kilder |
| `docs/sources/` | Dokumentation for hvert datasæts enheder, udtræk og forhold |
| `data/materials.sqlite` | Samlet database, gendannelig fra originaler og staging |
| `data/catalog.json` | Samlet statistik for den leverede database |

Vandkunsten-arkivet i de eksisterende `archive/`, `unpacked/` og `extracted/` bevares. De nye materialedata organiseres særskilt under `data/`.

## Tabeller

`sources` bevarer originalens identitet, udgiver, URL, hentetid, filsti, checksum, medietype og rettighedsstatus. `metadata_json` bevarer collectorens øvrige kildeoplysninger.

`materials` indeholder kildebestemte poster. Et generisk materiale, et konkret produkt og en sammensat konstruktion er forskellige `kind`-værdier. Poster fra forskellige kilder bliver ikke automatisk slået sammen, selv om navnet ligner. Et antal materialeposter er derfor ikke et antal unikke kemiske/fysiske materialer. Kategorisering er søgehjælp og kan være heuristisk.

`observations` forbinder materialeposten med en egenskab og en kilde. Den indeholder:

- `property`: egenskabens kode. Kildebestemte indikatorer, metoder og felter bevares.
- `value`: numerisk værdi, eller NULL når der ikke er en numerisk deklaration.
- `value_text`: den oprindelige numeriske tekst eller deklarationsmarkør.
- `unit`, `declared_unit`, `basis`: enhed og referencegrundlag.
- `module`: særskilt livscyklusmodul, hvor relevant.
- `method`, `data_status`: metode og angivelse af rapporteret/afledt værdi.
- `conditions_json`: eksempelvis fugt, temperatur, materialeretning, kildeår, testtilstand og anden kontekst.
- `source_id`, `source_locator`: original kilde og præcis lokation i den.
- `metadata_json`: hele den importerede observationspost, inklusive kildeafhængige ekstra felter.

`datasets` bevarer indsamlingsrapporterne. `build_info` bevarer skemaversion og SHA-256 for de anvendte JSONL-filer.

## Søgning og opslag

```sh
python3 materials.py stats
python3 materials.py search beton --limit 10
python3 materials.py search pine --category wood --limit 10
python3 materials.py show 'EN-ID-FRA-SOEGNINGEN'
python3 materials.py observations --material 'EN-ID-FRA-SOEGNINGEN' --limit 20
python3 materials.py observations --property density --limit 20
python3 materials.py observations --module D --limit 20
python3 materials.py sources --id 'EN-KILDE-ID'
```

`--limit` og `--offset` giver adgang til observationsresultater i sider. Egenskabsnavne og deres antal ses i `stats`. Forskellige kilder kan bruge forskellige koder for nært beslægtede egenskaber; navnene bliver ikke automatisk sidestillet. Kildenavne og originaldata kan også søges direkte i JSONL.

Søgning er tekstsøgning med små/store bogstaver og simple tegnvarianter håndteret. Det er ikke en automatisk oversætter eller et sikkert produktmatch. Vælg og verificér det konkrete datasæt før en beregning.

## Enheder og betingelser

Originale enheder bevares. Originaldatabasen er ikke generelt SI-normaliseret. Beregningsværktøjerne kan konvertere eksplicit understøttede enheder og skalere udvalgte GWP-observationer pr. modul; se [metoder og grænser](CALCULATIONS.md). Der dannes ikke en ukritisk livscyklustotal. Det forhindrer, at eksempelvis massefylde, arealvægt og produktvægt eller produktionsfase og modul D behandles som det samme.

Manglende værdier bliver ikke til nul. Der bevares både negative og eksplicitte nulværdier. Værdier fra forskellige fugttilstande, temperaturer, metoder, produkter og deklarerede enheder kan kræve forskellige anvendelser. En typisk eller simuleret materialeværdi er ikke automatisk en dimensionerende værdi eller en produktgodkendelse.

## Ny indsamling: gendannelse fra originaler og staging

```sh
python3 materials.py build
python3 materials.py verify
python3 -m unittest discover -s tests -v
python3 tests/verify_snapshot.py
```

Build læser JSONL som en strøm, kontrollerer originalfilerne med SHA-256 og kræver gyldige kildehenvisninger og entydige ID'er. En ny SQLite-fil erstatter kun den eksisterende, når import og integritetskontrol er lykkedes. En importfejl bevarer den eksisterende database.

`verify` kontrollerer alle registrerede originalers checksums samt SQLite-integritet og fremmednøgler. Det er en teknisk integritetskontrol; faglig anvendelighed skal også vurderes mod originalen og den konkrete opgave.

Collectors kan kræve allerede installerede `requests`, `openpyxl`, `pypdf` eller systemværktøjet `pdftotext`; selve database-CLI'et bruger kun Pythons standardbibliotek.

## Rettigheder

Hvert datasæt dokumenterer kilders licenser og begrænsninger. Kildens offentlige tilgængelighed er ikke automatisk en fri genudgivelseslicens. Manifest og originaler skal medtages i vurderingen før offentlig distribution. Et åbent softwareværktøj kan pege på kilder med forskellige datarettigheder.

## Brug fra agenter og modeller

En agent kan nu søge og hente dokumenterede værdier gennem CLI'et. Et korrekt næste trin er at koble identificerede modelmaterialer, mængder og enheder til bestemte databaseposter og bevare koblingens forudsætninger. Read-only udtræk fra BIMcraft/Solidcraft, navnebaserede kandidatforslag, eksplicitte kildebindinger og moduler til masse, GWP-skalering og træets fugtbevægelse er nu leveret og afprøvet. Automatisk produktækvivalens er ikke etableret; datavalg og betingelser skal stadig gennemgås. Se [kontrolrapporten](VALIDATION.md). De installerede programmer og deres eksisterende CLI/MCP er dokumenteret i wikien.
