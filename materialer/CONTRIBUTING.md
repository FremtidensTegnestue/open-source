# Bidrag til åbne materialedata

Bidrag er velkomne fra både fagfolk og udviklere. Du kan begynde med et [issue](https://github.com/FremtidensTegnestue/open-source/issues), hvis en forklaring er uklar, en kilde er ændret, eller et resultat kræver afklaring.

Vil du først prøve værktøjet, så brug [startvejledningen](docs/KOM-GODT-I-GANG.md). Du behøver ikke ændre kode for at bidrage: en konkret beskrivelse af, hvor du gik i stå, er også nyttig.

## Din første ændring

Arbejd i din egen kopi og en særskilt gren. Hold første ændring lille, fx en tydeligere forklaring eller en afgrænset fejlrettelse. En pull request skal forklare, hvad ændringen hjælper brugeren med, hvilke kontroller der er kørt, og hvad der stadig er uafklaret. Du behøver ikke skriveadgang til vores hovedgren for at arbejde videre på din egen udgave.

## Bidrag med data

Ved en rettelse af data skal du angive materiale-/observations-ID, original kilde, lokation i kilden, enhed og betingelser. Forskellige produkter eller metoder bliver ikke automatisk slået sammen. Bevar oprindelige værdier og deres proveniens.

Parquet-snapshottet ændres gennem en dokumenteret eksport, ikke ved at redigere enkelte binære filer i hånden. Kør `scripts/export_parquet.py` på en gennemgået database, kontroller manifestet, og medtag ændret dækning, kilder og versionsoplysninger. En ny dataversion skal have egne kontrolsummer og et tydeligt forhold til en eventuel færdig SQLite-release.

## Udvikl Rust-motoren

Den nuværende CLI er skrevet i Rust. Fra mappen `materialer`, med Rust **1.95 eller nyere** og Cargo installeret:

```sh
cargo test --locked --release
cargo run --locked --release -- --help
```

Disse kommandoer bygger program og tests og viser hjælpen. De kræver ikke, at du først bygger hele SQLite-grundbasen. Testene bruger blandt andet små, isolerede datalagre. Kildeafhængige tests kan være markeret `ignored`; det er ikke en bestået kontrol af de manglende kilder. [Rust-guide og dataudgaver](docs/RUST.md) · [Kode](src/) · [Tests](tests/)

## Udvikl Python-værktøjerne

Brug Python **3.11 eller nyere**, og opret et [lokalt Python-miljø](docs/KOM-GODT-I-GANG.md#2-slå-materialer-op-uden-database). Kør derefter fra mappen `materialer`:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Du behøver heller ikke bygge den store database før disse tests. Ved en ændring, der berører både Python og Rust, køres begge sæt tests.

Tests, som kræver de faktiske modelprogrammer, springes over, når CLI’erne ikke er installeret. En ændring af modelintegration skal også prøves med de relevante afprøvede versioner. [Det samlede eksempel](examples/integrated-workflow/README.md) viser en faktisk kontrol fra CAD til BIM, beregninger og returimport. [Hvad kontrollerne efterviser](docs/VALIDATION.md)

## Før du sender ændringen

Hold store lokale SQLite-filer, råarkiver, Python-miljøer, legitimationsoplysninger og midlertidige resultater uden for commits. Bevar tredjepartsangivelser. Se [dataguiden](data/README.md), [metoderne](docs/CALCULATIONS.md) og [THIRD_PARTY.md](THIRD_PARTY.md).
