# Mekaniske prøver af polymerer, kompositter, skum, halm og klæbestoffer

Samme plasttype kan opføre sig forskelligt som filament, sprøjtestøbt emne og printet del. En stålsnøret halmballe har en anden stivhed på højkant end fladtliggende. Her kan man følge sådanne forskelle ned til det konkrete prøveemne, målingen og originalkilden.

Supplementet indeholder **586 kildebelagte egenskaber for 303 materialeposter**. En post repræsenterer en bestemt recept, prøve eller forsøgsgruppe. De 92 spændings-tøjningskurver indeholder tilsammen **116.097 målepar**. Hver egenskab findes både som katalogfaktum og som søgbar observation. Begge repræsentationer henviser til samme måling.

## Hvad kan vi slå op?

| Prøvemateriale | Måling og afgrænsning | Original |
|---|---|---|
| 19 filamentprodukter til 3D-print | 169 resultater for trækmodul, trækstyrke og densitet. Referencefilament, enkelt ekstruderet fiber og prøveemner printet i 0° og 90° har særskilte poster. Prøvehastighed og produktbetegnelse følger trækresultatet. | [Aniskevich og Bulderberga, forsøgsregneark](https://doi.org/10.5281/zenodo.8089569) |
| PLA, PETG og PMMA fremstillet med FDM | 38 bøjeprøver med hver sin bøjestyrke og sit bøjningsmodul. Prøvekoden bevares, så man kan slå printbetingelserne op. | [Beníček, Vašina og Hrbáček, bøjeprøver](https://doi.org/10.5281/zenodo.14005312) |
| Ti elastomerer | 52 trækkurver og 40 trykkurver. Hver kurve bevarer filnavn, original rækkefølge, tøjning i procent og spænding i MPa. | [Roels, Costa Cornellà og Brancart, originale forsøgsfiler](https://doi.org/10.5281/zenodo.14983287) |
| Ensrettet glasfiber/epoxy med tre hærdeforløb | 23 trækudmattelsesforsøg samt E og trækstyrke fra fem statiske prøver. Lastgrænser, tværsnit, hærdning og registreret sluttilstand følger udmattelsestallet. | [Mikkelsen og Rasmussen, DTU, forsøgsplaner og resultater](https://doi.org/10.5281/zenodo.15665325) |
| Ni blandinger af polyurethanskum, herunder genanvendt skum | 18 trykspændinger ved 10 % og 25 % sammentrykning. For hver blanding følger vægtandelen af genanvendt skum fra byggeaffald. | [Elorza et al., tabel 5 og 6](https://doi.org/10.12688/openreseurope.13288.2) |
| Byggeisolering af ekspanderet polystyren, EPS | 22 forsøgsgrupper med målt tilsyneladende densitet og korttids-E-modul i tryk. Usikkerhed, prøvestørrelse og belastningsforløb følger værdierne. | [Vaitkus et al., tabel 1](https://doi.org/10.3390/ma15217548) |
| Sprøjtestøbt PLA, PA12, TPU og TPE | Otte recepter med eller uden 10 vægtprocent læderfibre. For hver findes trækmodul, trækstyrke og målt krybekomplians efter ti minutter ved 25 °C og 1 MPa. | [Nanni et al., tabel 4 og 7](https://doi.org/10.3390/polym13111837) |
| 30 upudsede rishalmballer med ståltrådsbinding | Fire tal pr. balle. Tilsyneladende densitet, E-modul og Poisson-forhold samt trykspænding ved lodret forskydning på en tredjedel af begyndelseshøjden. Geometri, orientering, 6,1 % begyndelsesfugt og prøvebetingelser følger hver post. | [Cao, Hu, Sun og Nie, tabel 1](https://doi.org/10.1155/2021/5557040) |
| Sikapower 4720, hærdet tokomponent-epoxylim | Målt trækmodul, flydespænding og trækstyrke på seks massive prøveemner samt forskydningsmodul og forskydningsstyrke på fem limsamlinger med ståldele. Forfatternes afledte Poisson-forhold har sin egen evidensbeskrivelse. | [Monteiro et al., tabel 1, tabel 3 og side 11](https://doi.org/10.1186/s40563-015-0056-y) |
| SS622, tokomponent-konstruktionssilikone til facadeglas | Den rapporterede Shore A-hårdhed samt de tre navngivne koefficienter til forskernes Mooney–Rivlin-model. Koefficienterne er tilpasset træk- og forskydningsforsøg og hører til ét parametersæt. | [Li et al., tabel 1 og afsnit 4](https://doi.org/10.3390/coatings16070775) |

## Brug i et projekt

En agent kan finde den konkrete produktbetegnelse, prøveretning og belastning i `conditions` og derefter åbne originalens `source_locator`. Usikkerhed kan være angivet som standardafvigelse, gennemsnitlig afvigelse eller konfidensinterval. Originalens definition følger hver tabel. Til analyser af en bygningsdel skal projektet også angive geometri, laster, indspænding og materialets faktiske tilstand. Anvendelse til dimensionering kræver dokumenterede værdier for det valgte byggeprodukt og anvendelsen.

- **Udmattelse** læses pr. prøve. Tre forsøg er eksplicit markeret som afsluttet uden brud. For EQA03-08 angiver forsøgsplanen 1.500.000 cyklusser uden afklaret sluttilstand. For EQA01-12 står den enkelte prøves frekvens tom. Enkelte oversigtsark og forsøgsplaner afviger med én cyklus. Kataloget bruger konsekvent planens kolonne L samt forsøgsnotatet.
- **Krybning** gælder den målte komplians under forsøgets belastning og varighed. En beregning over år kræver yderligere tids-, fugt- og temperaturdata.
- **Halmballer og skum** har feltet `compressive_stress_at_strain`. Belastningen angiver trykket ved en bestemt deformation. For halmballen 3C er kildens masse uforenelig med densitet og mål. Massen er udeladt. Densiteten er gengivet som i tabel 1 med en datakvalitetsnote.
- **Epoxy og fugemasse** kræver match mellem produkt, underlag, hærdning og prøvemetode. Epoxykildens Poisson-forhold er beregnet ud fra de målte E og G under antagelse af isotropi. Silikonens koefficienter skal bruges samlet med publikationens modelform og gyldige deformationsområde.

## Kilder, licenser og efterprøvning

Der ligger 22 originalfiler i `originals/`. De omfatter måleregneark, to arkiver med de rå trækkurver og trykkurver, tidsskriftsartikler i PDF eller XML samt tilhørende metadata. `sources.jsonl` krediterer forfatterne og registrerer versions-DOI, kildeadresse, konkret downloadadresse, hentningsdato, SHA-256 og licens. Artikler og forsøgsfiler er udgivet under CC BY 4.0. Zenodos fire separate metadataposter er CC0. Rishalmsartiklen linker til udgiverens DOI, og registeret angiver spejlet, som leverede selve udgiver-PDF’en. Katalogets ændringer består af udvælgelse af egenskaber, strukturerede forsøgsbetingelser og parring af observationer med katalogfelter. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Zenodos politik for åbne metadata](https://about.zenodo.org/policies/)

Fra `materialer/` med Rust-CLI’en installeret kan man indlæse supplementet og slå eksemplerne op.

```sh
ft-materials build --supplement data/supplements/mechanics-polymers --require-originals
ft-materials facts mechanics-polymers:material:cao-straw-3c --field compressive_stress_at_strain
ft-materials facts mechanics-polymers:material:li-ss622-silicone --field hyperelastic_coefficient
ft-materials facts mechanics-polymers:material:dtu-fatigue-eqa03-08 --field fatigue_resistance
```
