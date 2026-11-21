# Træsamlinger

To illustrerede fagbøger fra Fremtidens Tegnestue. Begynd med en bygningsdel, følg montagen, og åbn snittet gennem træet.

| Bog | Læs | Hent | Kapitler |
| --- | --- | --- | --- |
| Danske træsamlinger · Læs et hus gennem dets samlinger | [Indhold og modeller](danske/README.md) | [Dansk bog (PDF)](danske/bog.pdf?raw=true) | Lige stød, lige blad, hjørneblad, stolpens tap, kæmning og lask |
| Japanske træsamlinger · Forstå formen ved at samle den | [Indhold og modeller](japanske/README.md) | [Japansk bog på dansk (PDF)](japanske/bog.pdf?raw=true) | Koshikaketsugi, sogitsugi, aritsugi, aigaki, hirahozo og tome |

**Prøv de to bøger sammen.** Åbn [lige blad](danske/lige-blad/README.md) og [koshikaketsugi](japanske/koshikaketsugi/README.md). De har samme demonstrationsmål og synsvinkel. Følg sædet, skuldrene og den bevægelse, der kan åbne forbindelsen igen. Læs derefter de to kilders oplysninger om fastholdelse.

## Fra vidensbank til originalkilde

Vi brugte tegnestuens `vidensbank-soeg` til at finde tekst og billedopslag. Den danske tekstsøgning fandt blandt andet *Kortfattet Lærebog i Husbygning*, PDF-side 56 (trykt side 108–109). Den japanske kombinerede søgning fandt JAANUS’ egne opslag om koshikaketsugi, aigaki, sogitsugi og aritsugi. En separat billedsøgning gav også resultater fra andre byggeområder. Kildevalget bygger på læsning af den relevante originalside. Kapitelhenvisningerne fører til udgiveren.

```sh
vidensbank-soeg --tekst 'Tømrerarbejde lige blad lige hjørneblad svalehale blad tap taphul bindingsværk'
vidensbank-soeg 'Japanese joinery koshikaketsugi aritsugi aigaki hirahozo sogitsugi lap joint mortise timber drawings'
vidensbank-soeg --billeder 'Tømmer samlinger sidebillede lige blad hageblad hjørneblad tap svalehale'
```

## Hvad er efterprøvet?

Hvert kapitel indeholder en placeringsskitse, tre billeder af montagen, et snit og en redigerbar SolidCraft-model. Placeringsskitsens ring viser stedet i en større sammenhæng. Den detaljerede geometri er i de fire følgende billeder. Pilen viser den okkerfarvede dels bevægelsesretning.

Originalerne er sammenholdt med samlingens form, orientering og eventuel særskilt fastgørelse. Kapitlerne angiver, når forlægget viser en anden variant eller en nagle, et søm eller en anden fastholdelse, som er udeladt i undervisningsmodellen. Illustrationerne er vores egne. Alle mål i tabellen er valgte modelmål i mm. De angiver den samlede models omsluttende kasse langs X, Y og Z. De to bøger deler enkelte grundformer.

SolidCraft har kontrolleret, at alle legemer er lukkede, og at deres volumener svarer til de opstillede profiler. Interferenskontrollen er kørt med den bevægelige del i seks afstande fra slutstillingen (32, 16, 8, 4, 1 og 0 mm) langs den viste bane. Alle seks stillinger på hvert opslag gav nul overlap og nul ukontrollerede par. Det er en stikprøve langs en nominelt retlinjet montage. Der er ikke udført værkstedsprøver, dimensionering eller uafhængig tømrermæssig bedømmelse.

| Kapitel | Modelmål X × Y × Z (mm) | Dele |
| --- | ---: | ---: |
| [Lige stød](danske/lige-stoed/README.md) | 88 × 20 × 40 | 3 |
| [Lige blad](danske/lige-blad/README.md) | 92 × 20 × 16 | 2 |
| [Lige hjørneblad](danske/hjoerneblad/README.md) | 56 × 55 × 16 | 2 |
| [Stolpens lige tap](danske/tap/README.md) | 76 × 20 × 51 | 2 |
| [Kæmning ved kryds](danske/kaemning/README.md) | 84 × 74 × 26 | 2 |
| [Lask over et stød](danske/lask/README.md) | 84 × 18 × 20 | 3 |
| [腰掛継 · Koshikaketsugi](japanske/koshikaketsugi/README.md) | 92 × 20 × 16 | 2 |
| [殺継 · Sogitsugi](japanske/sogitsugi/README.md) | 86 × 20 × 14 | 2 |
| [蟻継 · Aritsugi](japanske/aritsugi/README.md) | 84 × 22 × 9 | 2 |
| [相欠 · Aigaki](japanske/aigaki/README.md) | 84 × 74 × 16 | 2 |
| [平ほぞ · Hirahozo](japanske/hirahozo/README.md) | 76 × 20 × 51 | 2 |
| [留 · Tome](japanske/tome/README.md) | 52 × 52 × 11 | 2 |

Kontrollér en model fra denne mappe med SolidCraft CLI.

```sh
solidcraft-cli eval danske/lige-blad/model.sc
solidcraft-cli run ../fagordbog/cad/kollision.json --in japanske/aritsugi/model.sc --results
```
