# Data og genopbygning

Kør fra mappen `materialer` med Python 3.11+. Direkte Parquet-opslag kræver kun `python -m pip install pyarrow==26.0.1`; de øvrige dataforløb bruger `pip install -r requirements.txt`.

| Script | Opgave |
| --- | --- |
| `opslag_parquet.py beton` | Vis et afgrænset materiale-/observationsuddrag og kilder direkte fra Parquet; ingen database eller beregning |
| `build_database.py` | Gendan hele SQLite-databasen fra de medfølgende Parquet-filer; ingen netværksdata kræves |
| `download_data.py` | Hent i stedet en færdig, komprimeret SQLite-database fra den fastlagte Release-version |
| `fetch_sources.py --demo` | Hent originale kildedokumenter til de medfølgende eksempler |
| `fetch_sources.py --all` | Forsøg at hente alle registrerede kildeoriginaler med kontrol af SHA-256 |
| `export_parquet.py SOURCE.sqlite OUTPUT_FOLDER` | Eksportér et nyt samlet snapshot med alle kolonner og efterprøvning |

Bygger og downloader bevarer en eksisterende database, medmindre `--force` gives. Begge arbejder med midlertidige filer og offentliggør først den nye database efter kontrol. Se [dataguiden](../data/README.md) for indhold og versioner.

Indsamling af nye data er en anden opgave end at installere det medfølgende snapshot. `collectors/` henter nyt kildegrundlag til `data/raw/` og strukturerede mellemdata til `data/staging/`; derefter kan `materials.py build` gendanne en database fra disse mellemdata. De originale arkivværktøjer `harvest.py` og `catalogue.py` vedrører Vandkunstens kildearkiv.
