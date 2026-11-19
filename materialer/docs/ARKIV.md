# Vandkunstens oprindelige værktøjer og kildearkivet

Vandkunstens [open source-side](https://opensource.vandkunsten.com/) var udgangspunkt for arbejdet. Den deler blandt andet regneark til tidlig klima-/økonomivurdering, et værktøj til træbevægelse og projektmateriale fra Lisbjerg Bakke.

Det offentlige repository indeholder vores kataloger og beskrivelser af materialet. Det komplette strukturerede **materialedatasæt** følger særskilt med i [data/parquet](../data/README.md). Det oprindelige **projekt-/softwarearkiv** er en anden samling: tredjepartsmodeller, PDF’er, regneark, makroer, billeder og plugins.

## Hent originalerne

Brug værktøjssidernes links til udgiveren. Hvis du vil opbygge det lokale HTTP-kildearkiv og de tilhørende tekst-/celleudtræk, kan du køre disse kommandoer fra mappen `materialer`.

```sh
python -m pip install -r requirements.txt
python harvest.py
python catalogue.py
```

`harvest.py` henter de registrerede sitefiler og direkte dokumentlinks. `catalogue.py` pakker lokale arkiver ud og laver søgbare udtræk. De kører ikke makroerne eller de oprindelige programmer. Et separat upstream-Git-snapshot eller alternativt hentede dokumenter er ikke automatisk hele indholdet af disse to trin; deres oprindelse står i `catalog/`.

`archive/`, `unpacked/`, `upstream/` og `extracted/` bruges lokalt og er ikke Git-filer i denne distribution. Udtrækslinks fra den historiske wiki går derfor til originalregnearket eller udgiverens projekt, når det lokale udtræk ikke følger med. Fane-, celle- og filoplysninger i kataloget hjælper med at finde det tilsvarende sted.

## Hvorfor adskille samlingerne?

Vores materiale-CLI kan bruges med de medfølgende Parquet-data uden at installere gamle Revit-plugins eller hente hele projektarkivet. Originalerne har samtidig forskellige rettigheder og afhængigheder. Eksempelvis er nogle værktøjer MIT-licenserede, dagslyspakken har en GPL-licens, og enkelte medfølgende plugins har andre betingelser. Se [THIRD_PARTY.md](../THIRD_PARTY.md).

[Katalog over projekter](../catalog/projects.json) · [Registrerede downloads](../catalog/downloads.json) · [Dataguide](../data/README.md)
