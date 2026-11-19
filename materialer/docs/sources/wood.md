# USDA Wood Handbook — træets fugt, bevægelse, varme og mekanik

Denne indsamling bygger på originale PDF-filer fra USDA Forest Service, Forest Products Laboratory: *Wood Handbook—Wood as an Engineering Material*, FPL-GTR-282, 2021. Kilden beskriver træ og træprodukter til blandt andet arkitekter og ingeniører. Der er ingen kobling til ét bestemt dansk produkt eller én styrkesorteret vare.

## Gemte originaler

| Fil | Original kilde |
| --- | --- |
| `data/raw/wood/chapter_04.pdf` | https://research.fs.usda.gov/download/treesearch/62243.pdf |
| `data/raw/wood/chapter_05.pdf` | https://research.fs.usda.gov/download/treesearch/62244.pdf |
| `data/raw/wood/chapter_13.pdf` | https://research.fs.usda.gov/download/treesearch/62261.pdf |
| `data/raw/wood/wood_handbook_2021.pdf` | https://www.govinfo.gov/content/pkg/GOVPUB-A13-PURL-gpo158673/pdf/GOVPUB-A13-PURL-gpo158673.pdf |

Publikationsoversigt: https://research.fs.usda.gov/fpl/wood-handbook . Den komplette original er bevaret som reference; kun de eksplicit beskrevne tabeller er struktureret. `sources.jsonl` registrerer URL, hentetid, originalsti, indholdstype og SHA-256 for hver PDF. `.txt`-filer ved siden af kapitlerne er afledte `pdftotext -layout`-udtræk og udgør ikke originalerne.

Direkte kapiteladresser på `www.fpl.fs.usda.gov` returnerede 403. De officielle alternative downloads på `research.fs.usda.gov` fungerede. Det fulde bind er desuden bevaret fra U.S. Government Publishing Office, 546 sider og cirka 103 MB.

## Strukturerede datapunkter

Det aktuelle udtræk indeholder 5.038 numeriske observationer, 325 kildeafgrænsede materiale-/artsregistre, 20 egenskabskoder og fire originalkilder. Materialeantallet er ikke et løfte om 325 forskellige biologiske arter: der findes artsgrupper, generelle referenceposter og separate kildeposter med beslægtede navne. Der udføres ingen automatisk global taksonomisk sammenlægning.

| Tabel | Indhold | Numeriske observationer |
| --- | --- | ---: |
| 4-1 | Vandindhold i grønt kerne- og splintved | 129 |
| 4-2 | Ligevægtsfugt som funktion af temperatur og relativ fugtighed | 423 |
| 4-3 | Radialt, tangentielt og volumetrisk svind fra grønt til ovntørt træ, amerikanske arter | 344 |
| 4-4 | Samme svindegenskaber for importerede arter/artsgrupper | 246 |
| 5-3a | Metric mekanik, amerikanske arter, grønt og 12 % fugt | 2.126 |
| 5-4a | Metric mekanik, canadiske arter, grønt og 12 % fugt | 297 |
| 5-5a | Metric mekanik, importerede arter, grønt og 12/15 % fugt som angivet | 905 |
| 4-7 | Relativ densitet samt varmeledningsevne og varmeresistivitet, ovntørt/12 % fugt | 340 |
| 4-8 | Specifik varmekapacitet ved temperatur og fugtindhold | 24 |
| 13-5 | Radiale og tangentielle dimensionsændringskoefficienter ved ændret fugt | 204 |

Mekanik omfatter relativ densitet, brudstyrke ved bøjning, elasticitetsmodul, arbejde til maksimal belastning, slagbøjnings-faldhøjde, tryk parallelt/vinkelret på fiber, forskydning, træk vinkelret på fiber og sidehårdhed, når den konkrete tabel har værdien.

## Betydning af fugt- og svinddata

Svind i tabellerne 4-3 og 4-4 er total ændring fra grønt til ovntørt træ, udtrykt i procent af dimensionen i grøn tilstand. Det må ikke bruges som en koefficient pr. procentpoint fugtændring.

Tabel 13-5 giver særskilte koefficienter pr. én procentpoints ændring i træfugt. De er baseret på en dimension ved 10 % træfugt og gælder inden for 6–14 % fugt. Kilden antager, at svind begynder ved 30 % fugt, dog 22 % for poster med fodnote b. Retning, referencefugt, gyldighedsinterval og fodnote er bevaret i `conditions`. Enheden `1/%MC` betyder pr. procentpoint træfugt, ikke pr. relativ ændring på én procent af fugtværdien. Ingen bevægelsesberegning udføres af denne collector.

Tabel 4-2 er en praktisk reference, primært afledt for Sitka-gran under oscillerende damptryksdesorption. Kilden understreger, at den viste opløsning på 0,1 procentpoint kun illustrerer tendenser; faktiske værdier varierer, og tabellen er ikke et grundlag for videnskabelig termodynamisk analyse. Disse begrænsninger følger observationerne.

## Enheder og faglige betingelser

Kildeenheder bevares: %, dimensionsløs relativ densitet (`1`), kPa, MPa, kJ/m³, mm, N, W/(m K), m K/W og kJ/(kg K). Der er ikke foretaget skjulte omregninger fra de separate inch-pound-tabeller. De er ikke importeret som ekstra kopier.

`value_text` er den originale numeriske celle med eventuelle tusindtalskommaer. `value` er den maskinlæsbare talværdi. Manglende streger og blanke felter bliver ikke til nul og bliver ikke udfyldt fra naboceller. Specifikt bliver relativ densitet i en grøn række ikke stiltiende kopieret til den følgende tørre række.

Alle observationer har PDF-sidetal, trykt kapitel-side, tabelnummer og række. Den originale kilderække er desuden bevaret i `conditions.source_line`. Speciesnavn, fugt, retning, region og de relevante kildeforbehold følger datapunktet.

Tabellerne i kapitel 5 omhandler små fejlfrie træprøver, ikke dimensioneringsværdier for styrkesorteret konstruktionstræ. Canadiske tørværdier er ifølge kildens fodnote justeret fra grønne værdier. Importerede værdier kommer fra verdenslitteraturen; nogle er justeret til 12 % fugt. Disse oplysninger fremgår af tabellen og bevares som fortolkningsgrundlag.

Varmeledningstabellen er omtrentlig; kilden angiver mulig variation på op til 20 %, og de tilknyttede relative densiteter er ikke artens gennemsnit. Varmeledning på tværs af fiber gælder omkring 24 °C i den beskrevne sammenhæng, hvilket er markeret som en omtrentlig referencetemperatur.

## Rettigheder

Der er tale om en amerikansk myndighedspublikation. Der er ikke i denne indsamling etableret en selvstændig licens for hvert citeret datasæt, tredjepartsbidrag eller illustration. Kildernes `license_status` er derfor konservativt `unknown`, med myndighedsophavet beskrevet; ingen fælles MIT- eller CC-licens er påført tabellerne. Originalernes ophavs- og litteraturoplysninger er bevaret.

## Gentag indsamlingen

Kør kommandoen fra mappen `materialer`.

```sh
python3 collectors/wood.py
```

Kræver Python 3 og Popplers `pdftotext`. Allerede gemte PDF'er genbruges; scriptet er en reproducerbar genudtrækning af denne udgave, ikke en automatisk kontrol af nye udgaver.

Scriptet kontrollerer tabelrækker og afviser uventede kolonneantal. Der er nul uafklarede parserejektioner i den aktuelle kørsel. Indbyggede referencechecks kontrollerer blandt andet rød el: 4,4 % radialt svind, 45.000/68.000 kPa bøjningsbrudstyrke grønt/12 % fugt; ligevægtsfugt 9,2 % ved 21,1 °C/50 % RH; merbau ved 15 % fugt; samt hvid ædelgrans tangentielle dimensionskoefficient 0,00245. Der kontrolleres også referencer og unikke observations-ID'er.
