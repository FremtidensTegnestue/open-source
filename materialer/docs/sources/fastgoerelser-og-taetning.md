# Skruer, beslag og tætning

Gennemgået 25. november 2026. [Åbn forløbet i browseren](https://fremtidenstegnestue.github.io/open-source/#fastgoerelser).

## Hvad kan beregnes nu?

To generiske skruereferencer er gjort tilgængelige i et særskilt browserudsnit af de eksisterende Parquet-data. Det ændrer ikke grunddatabasen eller BR18-opslagets 507 referencer. Der er ikke tilføjet nye faktorer til Rust-motoren.

| Valg | Præcis ÖKOBAUDAT-reference | Originalfilens SHA-256 |
| --- | --- | --- |
| Galvaniserede stålskruer | [889e2819-01be-4aa4-b7d3-d19e01e75c02, 20.26.070](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/889e2819-01be-4aa4-b7d3-d19e01e75c02?format=json&view=extended&version=20.26.070) | `5a6b5d6f6ef32c9037a8573e5d48a9f12290128521fbaaea0d695295dcddfc6e` |
| Rustfri stålskruer | [6c46fc8d-6a74-415b-8e6b-b90af72178ac, 20.26.070](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/6c46fc8d-6a74-415b-8e6b-b90af72178ac?format=json&view=extended&version=20.26.070) | `6bbb7969a62da7334489c088a6a2aa33ba509658c78fec10da747613132cf7e5` |

Begge filer er hentet igen og matcher repoets kilderegistrering byte for byte. De angiver Tyskland, referenceår 2023, datagyldighed til 2026 og EN 15804+A2 (EF 3.1). De valgte udgaver henviser til de foregående 20.23.050-udgaver. Der er ikke lavet en udtømmende undersøgelse af alle alternative skruekilder på markedet.

Kildeindikatoren hedder `Climate change`, UUID `a7ea142a-9749-11ed-a8fc-0242ac120002`. Originalens tyske indikatornavn identificerer den som GWP-total. Den må ikke forveksles med de særskilte fossil-/biogen-/luluc-indikatorer. Værdier, original tekst, enheder, referencebetingelser og kildeadresser bevares uændret.

Beregn med **skruernes nettovægt i kg**, ikke kassevægt eller antal. Metoden er `kildetal × nettovægt / 1 kg`, modul for modul. En skruetype kan ikke udskiftes alene ud fra klima: bæreevne, korrosion og montage bestemmer også det nødvendige produkt og antal. Referencerne gælder ikke søm, bolte eller beslag.

Galvaniserede skruer har A1–A3, C1, C2, C3 og D. Rustfri har A1–A3, C1, C2 og D. De øvrige C-faser står som ukendte; hverken fravær eller nul kg skaber et kildeoplyst nul. C2 indeholder kildens 50 km lastbiltransport efter brug. A4/A5/B er ikke tilføjet, og D er ikke modregnet. Undgå dobbeltregning af skruer i systemkilder og af kildens sluttransport.

Dataejer: Sphera Solutions GmbH; ÖKOBAUDAT udgives af BMWSB/BBSR. Originalerne angiver gratis anvendelse og henviser til ÖKOBAUDATs vilkår. [Uændret viderebrug kræver kildeangivelse](https://www.oekobaudat.de/en/database/search.html). Kildens egne licensfelter bevares; data ommærkes ikke til MIT. Faglig repræsentativitet og datagyldighed skal vurderes igen ved senere brug.

## Kilder fundet, men endnu ikke i browserberegningen

De følgende tre poster er kildekort, ikke færdige beregningsmaterialer. Originalerne hentes hos udgiveren; PDF'er og fulde produktdatasæt genudgives ikke her. Vilkår for offentlig viderebrug af udtrukne faktorer, konkret produktmatch og systemgrænser er fortsat åbne.

### Bjælkesko BSIN / Connectors

[Producentens BSIN-side](https://www.strongtie.dk/da-DK/produkter/bjaelkesko-bsin) viser variantvægt, fastgørelse, DoP og ETA. Den linker til [Connectors-EPD'en](https://ssttoolbox.widen.net/s/z6wdqnlhdr/epd-certificate-sst-connectors).

EPD-SST-20240583-IBC1-EN er udgivet 4. marts 2025, gyldig til 3. marts 2030. Referenceenheden er 1 kg installerede beslag, og kilden er et gennemsnit for producentens beslaggruppe. PDF-kontrolsum: `569b4c1aff4fcd40b85e1531097426737668c4647e1cccef4d4d2e303af3a715`.

Før beregning: bind den konkrete variant, antal og nettovægt til det anvendte klimagrundlag; afklar fastgørelsers placering i systemgrænsen. Produktets ETA og projektets samling skal vurderes særskilt. Gruppereferencen må ikke beskrives som et særskilt målt klimatal for hver variant.

### TESCON VANA

[Original EPD](https://proclima-pdm.moll-group.eu/documents/TESVAN/epd/epd.pdf): EPD-IES-0017291, version 1. oktober 2026, gyldig til 6. december 2029. Enheden er 1 m² tape med emballage. PDF-kontrolsum: `8fc87c199ffa1e344ddf1ed982bd79cb1761ae0d54850c17aee9031e3d1c88f2`.

Før beregning: bind produktvariant og tapebredde til løbende meter og opgør nødvendige overlap, primer og spild. Hold produktnetto og emballagemasse adskilt. A5 er deklareret og omfatter blandt andet emballagens biogene balance og klæberens tørring; samme bidrag skal ikke tilføjes igen. Et fund på gulvlimningstape kan ikke erstatte denne produktkilde.

### INTELLO

[Original EPD](https://proclima-pdm.moll-group.eu/documents/INT/epd/epd.pdf): EPD-IES-0017286, version 1. oktober 2026, gyldig til 6. december 2029. Enheden er 1 m² membran med emballage. PDF-kontrolsum: `ff96b26ac42eff2232078e5b19760b9555cce44dcb483513c8f677613bf81782`.

Før beregning: bind varianten og det nødvendige areal inklusive overlap til kilden. INTELLO PLUS har en anden EPD. Kildens håndtering af emballagens biogene balance i A1–A3 skal bevares. Funktion, fugtforløb og tætning af samlinger kræver egne vurderinger. En generisk dampspærres navn dokumenterer ikke fugtvariabel funktion.

Producentens [EPD-oversigt](https://int.proclima.com/company/sustainability/epd) omfatter flere programmer og udgaver. Bland ikke en nederlandsk MRPI-deklaration med en International EPD-udgave, selv om produktnavnet er det samme. De korte PDF-adresser kan ændre indhold senere; kontrollér version og kontrolsum ved en opdatering.
