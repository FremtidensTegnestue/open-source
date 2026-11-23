# Kom hurtigt i gang med materialedata

**[Begynd i browseren uden installation](https://fremtidenstegnestue.github.io/open-source/).** Her kan du søge blandt 507 danske tabel 7-referencer, åbne deres tal og kilder og gemme materialedata. Det er første browserudgave med kildedata fra 2025; det større Parquet-grundlag og beregningsværktøjet nedenfor har et andet omfang.

Begynd med et færdigt eksempel. Gå videre til materialeopslag, når du vil undersøge dine egne muligheder. Du behøver først en database eller et modelprogram, når opgaven kræver det.

Projektets egen kode og tekst er udgivet under [MIT](../../LICENSE). **Kildedata og tredjepartsdokumentation beholder deres egne vilkår**; se [kilder og rettigheder](../THIRD_PARTY.md).

## Vælg dit næste trin

| Trin | Hvad du får | Tid, groft skøn | Data og plads | Kræver |
| --- | --- | --- | --- | --- |
| [1. Læs eksemplet](#1-læs-eksemplet) | Forstå model → mængde → kilde → resultat | 10 min | Ingen lokal installation | Browser |
| [2. Slå materialer op](#2-slå-materialer-op-uden-database) | Se værdier, enheder og kilder direkte fra Parquet | 10 min efter download | Ca. 91 MB Parquet, plus projekt og Python-miljø | Python 3.11+ og pyarrow |
| [3. Brug beregningsværktøjet](#3-brug-beregningsværktøjet-efter-behov) | Aktuelle dataudgaver, beregninger og kontrol | Afhænger af installation og maskine | Ca. 9 GB til grundbasen, plus byggeplads og tillæg | Rust 1.95+ og Cargo |
| [4. Brug en model](#4-brug-en-model-valgfrit) | Hent mængder fra SolidCraft eller BIMCraft | Efter behov | Afhænger af model og program | Modelprogrammernes CLI’er installeres separat |

Pladstallene beskriver dataene, ikke hele installationen. En Git-kopi henter også dokumenter og eksempler; Python-pakker, Rust-kompilering og midlertidige databaseindeks kræver ekstra plads. Vi angiver derfor ikke 10 GB som et sikkert samlet minimum.

## 1. Læs eksemplet

Åbn [betonpladen med to stålskinner](../examples/integrated-workflow/README.md). Intet skal installeres.

Når pladens tykkelse ændres fra 100 til 120 mm, stiger den samlede masse fra **cirka 336 til 401 kg** og det beregnede klimabidrag i **A1–A3 fra cirka 55,3 til 62,2 kg CO₂e**. Eksemplet viser, hvor mængder, materialevalg og kildeværdier kommer fra.

Tallene gælder de tre dele og deres valgte generiske referencer. A1–A3 beskriver her produktionen; resultatet er en klimadelsum. En komplet bygnings-LCA kræver flere dele, faser og forudsætninger.

## 2. Slå materialer op uden database

Parquet er et kompakt tabelformat. Du kan læse de medfølgende filer direkte med Python. **Dette er den lette lokale vej til opslag i hele Parquet-grundlaget; browseropslaget ovenfor har et mindre, dansk referenceudsnit.**

Hent projektet fra [GitHub](https://github.com/FremtidensTegnestue/open-source) via **Code → Download ZIP**, eller brug Git:

```sh
git clone https://github.com/FremtidensTegnestue/open-source.git
cd open-source/materialer
```

Åbn en terminal i mappen `materialer`. Opret og aktivér et lokalt Python-miljø.

**macOS/Linux:**

```sh
python3 -m venv .venv
. .venv/bin/activate
```

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Vælg din installerede Python-version, hvis den er nyere end 3.11. Hvis PowerShell afviser aktivering, kan du skrive `.\.venv\Scripts\python.exe` i stedet for `python` nedenfor.

Installér derefter den afprøvede pakke og kør det færdige [opslagsscript](../scripts/opslag_parquet.py):

```sh
python -m pip install pyarrow==26.0.1
python scripts/opslag_parquet.py beton
python scripts/opslag_parquet.py egetræ
```

### Se, om dit første opslag virker

Ved `egetræ` skal du finde **`br18:t7:G0407:row260`**, med navnet »Træ, egetræ (12% fugt / 10,7% H2O)«. Dets densitetsobservation har `value: 716.8` og `unit: kg/m³`. Kilden er BR18's generiske tabel 7 fra 2025, celle `Sheet1!K260:L260`; URL og rettigheder vises nederst. Det er denne references tal, ikke en kontrol af dit eget træprodukt.

Du ser også klimaværdier for flere livscyklusmoduler. De vises hver for sig og bliver ikke automatisk summeret. Et negativt produktionstal for træ er ikke en komplet klimaberegning.

Du skal ikke skrive et script selv, bygge SQLite eller hente nye originalkilder. Opslaget læser kun `data/parquet/` og foretager ingen beregning eller enhedsomregning.

Det viser højst fem navnetræf, et afgrænset uddrag på højst 12 observationer og kilderne til netop disse observationer. Et navnetræf er en kandidat, ikke et godkendt produktmatch. Vælg et konkret ID fra listen, når du vil undersøge én post nærmere:

```sh
python scripts/opslag_parquet.py --material-id br18:t7:G0407:row260
python scripts/opslag_parquet.py beton --limit 10 --observations 20
```

### Læs en værdi sammen med dens grundlag

| Felt | Hvad du skal se efter |
| --- | --- |
| `value`, `value_text`, `unit` | Tal, bevaret tekst/markør og enhed. `None` i `value` betyder, at der ikke står én numerisk værdi dér; læs også teksten og status. |
| `declared_unit`, `basis` | Hvilken mængde eller reference tallet gælder for, fx 1 kg, 1 ton eller 1 m² af en bestemt konstruktion. |
| `module` | Livscyklusfasen. Forskellige moduler må ikke behandles som samme beregningsomfang. |
| `method`, `conditions_json`, `data_status` | Metode, betingelser og om værdien er rapporteret eller afledt. |
| `source_id`, `source_locator` | Kildens identitet og den konkrete celle eller placering. Scriptet viser også URL, registreret kontrolsum og rettigheder fra `sources.parquet`. |

Et negativt A1–A3 for træ er ikke dokumentation for et samlet negativt klimaaftryk. Manglende oplysninger bliver ikke til nul. Den viste kontrolsum er registreret kildeinformation; dette lille opslag henter eller efterprøver ikke originalfilen.

### Grunddata og nyere tillæg

Parquet-grundlaget indeholder cirka **1,99 millioner observationer**, heraf cirka **1,96 millioner fra ÖKOBAUDAT**. De præcise antal og kontrolsummer står i [Parquet-manifestet](../data/parquet/manifest.json).

Direkte Parquet-opslag læser **ikke de nyere tillæg**, fx ekstra mekanik-, levetids- og driftsdata. Den aktuelle Rust-udgave kombinerer grundlaget med de offentlige tillæg; se [dataudgaven og optællingerne](../data/releases/mechanics-2026-11-20.json). Danske produktdeklarationer fra EPD Danmark distribueres ikke som åbne produktdata i Git; de kan indsamles lokalt efter den særskilte vejledning.

### Hvis du går i stå

| Det, du ser | Næste handling |
| --- | --- |
| `Mangler pyarrow` | Kør installationen med samme `python`, som du bruger til opslaget. På Windows kan du bruge `.\.venv\Scripts\python.exe` til begge kommandoer. |
| `can't open file` eller »filen findes ikke« | Kontrollér, at terminalen står i `materialer`, og at `scripts/opslag_parquet.py` findes i din download. |
| `Ingen træf` | Prøv et kortere navn eller det konkrete ID ovenfor. Mange kildenavne er på engelsk eller tysk; søgningen oversætter dem ikke. |

Virker det stadig ikke, så [opret et issue](https://github.com/FremtidensTegnestue/open-source/issues) med kommandoen, fejlteksten, dit operativsystem og resultatet af `python --version`. Undlad kundedata, adgangsnøgler og private modeller. Du kan fortsat læse eksemplet fra trin 1 i browseren.

## 3. Brug beregningsværktøjet efter behov

Vælg den aktuelle [Rust-guide](RUST.md), når du vil bruge de samlede data, beregne et bidrag eller kontrollere et modelgrundlag. Fra mappen `materialer`, med Rust 1.95+ og Cargo installeret:

```sh
cargo install --locked --path .
ft-materials build
ft-materials status
ft-materials search egetræ --limit 5
```

Dette trin bygger og aktiverer en lokal dataudgave. Grundbasen fylder omkring 9 GB; beregn ekstra plads til kompilering, indeks og tillæg. Rust-guiden skelner mellem [aktuel kode og de tidligere Linux-udgivelser](RUST.md#vælg-program-og-data-fra-samme-udgave). Brug en motor bygget fra samme checkout som dataene til de nyeste tillæg; et program fra en ældre udgivelse dækker ikke automatisk den aktuelle dataudgave.

Den [detaljerede Python-vej fra v0.1](PYTHON-V01.md) er bevaret til det historiske forløb. Den gendanner Parquet-grundbasen og giver ikke automatisk samme tillæg og metoder som den aktuelle Rust-motor.

## 4. Brug en model, valgfrit

SolidCraft og BIMCraft installeres separat. Du kan begynde med [det gennemførte modelforløb](../examples/unified-workflow/README.md). Det er et eksempel med konkrete bindinger og begrænsninger.

Betonpladeeksemplet er afprøvet med SolidCraft CLI 0.44.0 og BIMCraft CLI 0.12.0. Kontrollér den CLI, terminalen faktisk vælger; en opdateret app kan eksistere ved siden af en ældre terminalinstallation. FieldCraft er et separat program til de dokumenterede statiske delundersøgelser, fx [hyldeeksemplet](../examples/hyldekonsol/README.md). Der følger ikke adaptere til Revit, ArchiCAD eller Rhino med denne integration.

## Brug en AI-agent

Åbn mappen `materialer` i en agent med adgang til lokale filer og terminal. Du kan begynde med:

> Læs README.md og docs/KOM-GODT-I-GANG.md. Brug kun Parquet-filerne i data/parquet; byg eller aktivér ingen database. Slå [materiale] op med scripts/opslag_parquet.py. Vis tal og value_text sammen med enhed, declared_unit, basis, modul, metode, betingelser, status og kilde. Følg source_id til URL, rettigheder og registreret kontrolsum. Fortæl, hvad der mangler, før værdien kan bruges til [formål]. Gæt ikke, og behandl ikke navnetræf som et godkendt materialevalg.

Den [medfølgende materialeskill](../.agents/skills/material-model-assessment/SKILL.md) kan bruges, når du går videre til et egentligt beregnings- eller modelforløb. En agents adgang til filer og programmer afhænger af dens opsætning; en almindelig chat har ikke automatisk lokal adgang.

Den [maskinlæsbare vejvisning](../kom-i-gang.json) beskriver de samme veje og afgrænsninger. Den installerer ikke noget.

## Før du sammenligner

- Kontrollér samme funktion, referenceenhed, indikator, modul, metode og relevante betingelser. Poster fra forskellige kilder er ikke harmoniseret alene ved at ligge i samme datasæt.
- Et materialetal er ikke automatisk et produktmatch eller et dimensioneringsgrundlag.
- Kontrollér den enkelte kildes vilkår før videredistribution: [licensarkivet](../data/licenses/) og [THIRD_PARTY.md](../THIRD_PARTY.md).

[Ordliste](ORDLISTE.md) · [Datamodel](DATABASE.md) · [Beregningsmetoder](CALCULATIONS.md) · [Aktuel Rust-guide](RUST.md)
