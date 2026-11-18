# Brug materialedata fra Rust

Kør kommandoerne fra den mappe, hvor du har pakket projektet ud. Du kan også angive dens placering med `ft-materials --root /sti/til/open-source status`. På en maskine med Rust 1.95 eller nyere og Cargo kan du installere CLI'et én gang. Har du hentet en færdig binærfil fra projektets udgivelser, kan du begynde ved `ft-materials build`.

```sh
cargo install --locked --path .
ft-materials build
ft-materials status
ft-materials search egetræ --limit 5
```

Grundlaget kommer fra de komplette Parquet-filer i Git. Den første bygning læser cirka to millioner observationer og opretter en fælles SQLite-base på omkring 9 GB. Beregn ekstra ledig plads til indeks under bygningen. Hver ny dataudgave deler denne base og får sin egen lille SQLite-fil med tillæg. Det gælder også den udvidede lokale udgave med EPD Danmark. Materialeopslag og beregninger køres lokalt. Rust-programmet læser selv Parquet, SQLite, PDF og XLSX. Modelarbejdet bruger de to modelprogrammers CLI'er.

## Slå en konkret egenskab op

```sh
ft-materials lookup tampere:material:D1 --property property:thermal_conductivity
ft-materials observations --property property:density --dataset tampere --limit 3
ft-materials source tampere:source:17778563:materialProperties.zip
ft-materials calculate examples/requests/environmental-1000kg.json
```

Det første opslag finder en hel kurve. I prøve D1 svarer x-værdien 0,65 til 65 % relativ luftfugtighed. Det tilhørende målepunkt er 0,0351 W/(m·K) ved 10 °C. Observations-ID, rå enhed, originalfilens kontrolsum og placering i kildens JSON følger med. Klimaberegningen i sidste linje giver 429,5 kg CO₂e i modul A1 for eksemplets 500 kg.

## Tag EPD Danmark med

```sh
ft-materials collect-epd --locked
ft-materials build --supplement data/supplements/tampere --supplement data/staging/epd-danmark --require-originals
ft-materials observations --property property:gwp_total --dataset epd-danmark --module A1-A3 --limit 3
```

Den første kommando henter de låste originaler fra udgiveren og gemmer dem lokalt med SHA-256. Den anden aktiverer udgaven med begge tillæg. Angiver du selv `--supplement`, udgør de angivne mapper hele listen over tillæg. Udgavens ID og optællinger står i svaret. En ændret PDF kan undersøges i en separat, ny indsamling. [EPD-vejledning og afgrænsning](../data/supplements/epd-danmark/README.md)

## Fælles model for data

| Begreb | Hvad modellen gemmer |
| --- | --- |
| Materialepost | Kildens præcise referent, et produkt, en opbygning, et simuleringsinput eller en prøve. Hver post har eget ID og en materialefamilie til søgning. |
| Egenskab | Et fælles egenskabs-ID og kildens eget feltnavn. Eksempelvis kan varmeledning findes på tværs af biblioteker. Ukendte felter får et ID, der omfatter deres datasæt. |
| Observation | Kildens tal, interval, klassifikation, tekst, hel kurve eller manglende værdi. Enhed, oprindelig tekst, metode, betingelser, modul og deklareret mængde følger observationen. |
| Kilde og kildeversion | Stabil kildereference, URL, rettigheder og SHA-256 for originalen. Et opslag peger på en bestemt celle, PDF-række eller sti inde i originalen. |
| Dataudgave | En uforanderlig kombination af grundlag, tillæg, skema og egenskabsordbog. Projektets valg gemmer ID'et på denne kombination. |

Et fælles egenskabs-ID gør det muligt at finde flere kilders værdier. Arkitekten eller agenten vælger den relevante observation ud fra produkt, metode og betingelser. Bruttodensitet og densitet kan fx slås op separat. Et opslag på en art eller en materialefamilie godkender ikke egenskaberne for en konkret byggevare. [SQL-skema](../data/unified/schema.sql) · [Egenskabsordbog](../data/unified/vocabulary.json)

## Nye kildetal og gamle projekter

```sh
ft-materials check-updates --source br18:source:table-7-2025.xlsx
ft-materials check-updates --dataset tampere
ft-materials verify
```

Kildetjekket henter de valgte registrerede adresser og sammenligner filernes aktuelle indhold med udgavens SHA-256. Svaret skelner mellem identiske filer, ændrede filer og adresser, der ikke kunne kontrolleres. Nye URL'er i EPD-kataloget opdages via indsamlerens `--refresh`. Kildetjek kan køres efter behov eller fra tegnestuens almindelige tidsstyring. En opdatering af kilden ændrer først beregningsgrundlaget, når man bygger og vælger en ny udgave.

`ft-materials status` viser det fulde ID. Brug `--snapshot ID` på senere opslag for at genskabe dem. `ft-materials changes GAMMELT_ID NYT_ID` sammenligner originalernes versioner. Tilføj `--selection materialevalg.json` for at se, hvilke valgte observationer på hvilke modeldele der er berørt. `build --expect ID` afviser andre input end dem, der skabte den aftalte udgave. `verify` gennemlæser begge databasefiler og sammenligner deres kontrolsummer med den installerede udgaves manifest.

## Beregn ud fra modeller

```sh
ft-materials build --base-only --no-activate
ft-materials assess examples/unified-workflow/revised/model.sc --software solidcraft --selection examples/unified-workflow/selection.json --transfer examples/unified-workflow/revised/transfer.json
```

Se filnavne og kommandoer til begge modelprogrammer i [det gennemførte forløb](../examples/unified-workflow/README.md). Velkendte modeldele deler det samme materialevalg på tværs af programmerne. En ny modelrevision kræver et kort over dens faktiske dele. Ved deling eller manglende identitet får agenten uafklaret status. CLI'et returnerer JSON, kode 0 for succes og kode 2 for delvise modelresultater.

## Byggeplads på disken

Cargo bygger med højst tre samtidige jobs, uden inkrementelle mellemprodukter og uden debugsymboler i projektets standardprofiler. Brug én `CARGO_TARGET_DIR` pr. vedligeholdt checkout, hvis du selv udvikler på CLI'et. Efter installationen kan `cargo clean` i denne checkout fjerne de genopbyggelige filer fra den valgte target-mappe. Efter en afbrudt dataimport rydder næste bygning også genkendelige, ufuldstændige arbejdsmapper under datalagerets byggelås. Kildearkivet under `data/raw` og de fastlåste databaser under `data/editions` har deres egen levetid og indgår ikke i Cargo-cachen.

[Udgivelsens tre faste ID’er og inputkontrolsummer](../data/releases/unified-v0.2.0.json) · [Færdige programmer til Linux](https://github.com/FremtidensTegnestue/open-source/releases/tag/v0.2.0)
