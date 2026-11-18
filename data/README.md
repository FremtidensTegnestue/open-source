# Hele datasættet — Parquet og SQLite

Brug `ft-materials build` fra projektets rod for den offentlige Rust-udgave. Den kombinerer Parquet-grundlaget med versionsstyrede tillæg. `supplements/` indeholder kilderegistre, observationer og eksternt dokumenterede feltværdier som JSONL eller komprimeret JSONL. Fjernede eller lokalt tilføjede tillæg giver en anden dataudgave. [Feltkatalog og mål](../docs/MATERIALEFELTER.md) · [Aktuelle udgaver og optællinger](releases/unified-v0.3.0.json) · [Installation og brug](../docs/RUST.md)

**Tallene følger med projektet.** Mappen [parquet/](parquet/) indeholder alle 1.985.582 observationer, 11.161 materiale-/produktposter, 7.135 kilder og fire datasæt fra snapshot 17. november 2026. Alle tabeller og kolonner er med; ingen materialegruppe er fjernet for at gøre pakken lille.

## To formater af samme snapshot

| Format | Rolle | Målt størrelse |
| --- | --- | ---: |
| Parquet, komprimeret med Zstandard | Versionsstyret datagrundlag i dette Git-repository; velegnet til analyse | 90.628.421 bytes i 15 datafiler |
| SQLite | Lokal arbejdsdatabase til søgning, beregninger og agenter | 8.780.214.272 bytes |
| SQLite, komprimeret med Zstandard | Valgfri færdig database på GitHub Releases | 186.747.349 bytes |

Størrelsesforskellen skyldes lagring, komprimering og SQLite-indekser. Parquet-udgaven har **samme værdier og samme kolonner**, inklusive de oprindelige JSON-felter med betingelser og metadata. Parquet- og SQLite-udgaverne vedligeholdes ikke manuelt hver for sig: et versionsmanifest binder snapshot og kontrolsummer sammen.

## Genskab den historiske v0.1-database

```sh
python -m pip install -r requirements.txt
python scripts/build_database.py
python materials.py verify --database-only
python materials.py search beton --limit 5
```

Databasen gendannes lokalt fra de Parquet-filer, du allerede har hentet med projektet. Der foretages ingen nye materialeopslag på nettet. Sørg for cirka 10 GB ledig diskplads; den fuldt validerede genopbygning tog cirka 72 sekunder på vores maskine.

Har du en eksisterende database, bliver den bevaret. Du kan vælge et andet output med `--db sti/til/ny.sqlite`. `--force` udskifter først en eksisterende database, når den nye har bestået kontrollen.

Alternativt kan du hente den færdige database fra [version v0.1.0](https://github.com/FremtidensTegnestue/open-source/releases/tag/v0.1.0):

```sh
python scripts/download_data.py
```

Downloaderen kontrollerer både komprimeret og udpakket størrelse og SHA-256 samt SQLite-integritet før installation. Versionsadressen og kontrolsummerne står i [releases/2026-11-17.json](releases/2026-11-17.json).

## Organisation

```text
data/
├── README.md
├── parquet/
│   ├── manifest.json
│   ├── datasets.parquet
│   ├── sources.parquet
│   ├── materials.parquet
│   ├── build_info.parquet
│   └── observations/
│       ├── dataset_id=br18/
│       ├── dataset_id=environmental/
│       ├── dataset_id=technical/
│       └── dataset_id=wood/
├── releases/
│   ├── 2026-11-17.json
│   └── parquet-validation-2026-11-17.json
├── licenses/                  # bevarede kildevilkår
└── materials.sqlite          # gendannes lokalt; ikke en Git-fil
```

Observationer opdeles efter kildeområde og i filer med højst 250.000 rækker. Den største aktuelle datafil er cirka 11,2 MB. Kolonnen `dataset_id` er også gemt i selve filerne. SQLite-skema og indeksdefinitioner ligger i Parquet-manifestet, så genopbygningen ikke skal gætte typer eller relationer.

## Hvad er kontrolleret?

[Manifestet](parquet/manifest.json) indeholder filkontrolsummer, rækker, kolonner, NULL-optællinger og logiske indholdshashes pr. tabel/partition. Eksporten læste alle kolonner tilbage og sammenlignede hver række. Genopbygningen kontrollerede igen alle Parquet-rækker og alle gendannede SQLite-celler samt fremmednøgler og databaseintegritet.

Kontrollen bevarede blandt andet 159.038 negative tal og 902.715 eksplicitte nuller. Manglende data er fortsat NULL eller kildens deklarationsmarkør; de bliver ikke til nul. Se [genopbygningskontrollen](releases/parquet-validation-2026-11-17.json).

## Brug Parquet direkte

Python med PyArrow:

```python
from pathlib import Path
import pyarrow.dataset as ds

root = Path("data/parquet/observations")
observations = ds.dataset(root, format="parquet", partitioning=None)
density = observations.to_table(
    columns=["material_id", "value", "unit", "conditions_json", "source_id"],
    filter=ds.field("property") == "density",
)
print(density.slice(0, 10).to_pylist())
```

Vælg kolonner og filtre, før du indlæser store tabeller. Forskellige densiteter, enheder og fugtbetingelser er ikke automatisk sammenlignelige. Bruger du Hive-partitionering i et andet analyseværktøj, skal du tage højde for, at `dataset_id` allerede findes i datafilerne.

## Kilder og originale dokumenter

Tabellen `sources` bevarer URL, udgiver, hentetid, originalens relative filsti, SHA-256 og kildebestemte rettighedsoplysninger. `observations` bevarer den præcise kildelokation, enhed, metode, modul og betingelser. Det store lokale kildearkiv og rådatafiler er særskilte fra det komplette strukturerede datasæt.

For de originaler, der bruges i de medfølgende eksempler:

```sh
python scripts/fetch_sources.py --demo
```

Dette henter dokumenterne til eksemplerne, ikke en mindre database. `--all` forsøger at hente alle registrerede originaler; ældre udgiveradresser kan være flyttet. En ændret fil bliver ikke accepteret som den gamle original. `materials.py verify` kræver alle originaler; `verify --database-only` kontrollerer alene databaseintegritet og påstår ikke at have verificeret kildefilerne.

## Licenser og anvendelsesbetingelser

**Koden og kildedataene har forskellige vilkår.** Der er ikke tildelt en ny fælles MIT- eller CC-licens til den samlede datamængde. Oprindelige kildeoplysninger og afvigende/ukendte licensfelter følger med i begge formater. ÖKOBAUDAT beskriver distribution af uændrede data med kildeangivelse i sine [officielle vilkår](https://www.oekobaudat.de/no_cache/en/database/search.html); individuelle kildefelter og metodiske begrænsninger er også bevaret.

Læs [THIRD_PARTY.md](../THIRD_PARTY.md), [datadækningen](../docs/COVERAGE.md) og [kildedokumentationen](../docs/sources/). Et offentliggjort tal er ikke automatisk et egnet dimensioneringsgrundlag eller et korrekt produktmatch.

## Feltdata i v0.3

| Kilde eller format | Hvad der følger med |
| --- | --- |
| [Danske referencer](../docs/sources/danske-levetider.md) | Energistyrelsens scenarier i Git. BUILDs fire detaljeringsniveauer kan indlæses fra originalen til lokal brug. |
| [Driftsudsagn](../docs/sources/operations.md) | Offentlige feltregistreringer og originale procesdata. Danske deklarationer og fabrikantmanualer hentes fra udgiverne. |
| [Målinger, genbrug og priser](../docs/sources/field-sources.md) | Kildefiler, herunder forsøgsdata, donorinventarer, egenskabstabeller og historiske råvarepriser med angivet marked. |
| [Gennemgang af miljødata](../docs/sources/oekobaudat-review.md) | Den gennemgang, som hver udgiver har registreret for sin procesversion, med kilde og reviewerreference. |
| [Aktive feltdefinitioner](../docs/MATERIALEFELTER.tsv) | Dansk navn, felt-ID, anvendelsesniveau, værdiform, enhed og betydning. |
