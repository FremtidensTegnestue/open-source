# Bidrag til åbne materialedata

Bidrag er velkomne fra både fagfolk og udviklere. Du kan begynde med et [issue](https://github.com/FremtidensTegnestue/open-source/issues), hvis en forklaring er uklar, en kilde er ændret, eller et resultat kræver afklaring.

Ved en rettelse af data skal du angive materiale-/observations-ID, original kilde, lokation i kilden, enhed og betingelser. Forskellige produkter eller metoder bliver ikke automatisk slået sammen. Bevar oprindelige værdier og deres proveniens.

Ved kodeændringer:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Tests, som kræver de faktiske modelprogrammer, springes over, når CLI’erne ikke er installeret. En ændring af modelintegration skal også prøves med de relevante afprøvede versioner. [Det samlede eksempel](examples/integrated-workflow/README.md) viser en faktisk kontrol fra CAD til BIM, beregninger og returimport.

Parquet-snapshottet ændres gennem en dokumenteret eksport, ikke ved at redigere enkelte binære filer i hånden. Kør `scripts/export_parquet.py` på en gennemgået database, kontroller manifestet, og medtag ændret dækning, kilder og versionsoplysninger. En ny dataversion skal have egne kontrolsummer og et tydeligt forhold til en eventuel færdig SQLite-release.

Hold store lokale SQLite-filer, råarkiver, Python-miljøer, legitimationsoplysninger og midlertidige resultater uden for commits. Bevar tredjepartsangivelser. Se [dataguiden](data/README.md), [metoderne](docs/CALCULATIONS.md) og [THIRD_PARTY.md](THIRD_PARTY.md).
