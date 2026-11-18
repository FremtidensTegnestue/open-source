# Fugt og varme i byggematerialer fra Tampere

De 43 materialeprøver omfatter blandt andet gips, krydsfiner, træfiber, glasuld, stenuld, hørisolering og membraner. Du kan slå en prøves densitet op og se, hvordan den publicerede varmeledning ændrer sig med luftens relative fugtighed. Materialets produktnavn og producent gælder for prøven i det finske studie.

Antti Mikkonen og Juha Vinha, Tampere University Building Physics, udgav samlingen i 2025. Projektet her har oversat kildens struktur til materiale- og observationsposter, bevaret de publicerede tal og tilføjet kildehenvisninger ind i originalfilen. Udgiverens licens er CC BY 4.0. [Originaludgivelsen, version 1.0.0](https://doi.org/10.5281/zenodo.17778563) · [Licens](https://creativecommons.org/licenses/by/4.0/)

## Hvad følger med?

| Indhold | Antal |
| --- | ---: |
| Materialeprøver | 43 |
| Tal med enhed | 196 |
| Hele kurver | 387 |
| Par af relativ luftfugtighed og egenskabsværdi på kurverne | 3.329 |
| Tykkelsesfelter, hvor kilden angiver `NaN` | 19 |

Hver kurve er én observation. Fugtaksen er en andel fra 0 til 1. For eksempel svarer 0,65 til 65 % relativ luftfugtighed. For prøve D1 angiver kilden varmeledning 0,0351 W/(mK) ved dette punkt og +10 °C. Flere kurver hører til samme prøve, blandt andet sorption, adsorption og desorption. Opslagene bevarer hver serie og dens måleenhed. De 19 tomme tykkelser indgår med status `missing` i [observationsfilen](observations.jsonl).

For 258 kombinationer af prøve og egenskab er primærfilen tillige sammenholdt med den supplerende projektmappe i ZIP-filen. 71 stemte præcist i prøvens ID, værdier og eventuel fugtakse. Her følger regnearkets angivelse af temperatur eller tør densitet med som en betingelse. 79 sammenligninger viste forskelle, 96 manglede tal i regnearket, og i 12 tilfælde manglede materialet på regnearket. Dets ekstra testblanding D67 findes kun dér. Kildeplacering og forskelle fremgår af [sammenligningen](workbook-comparison.jsonl).

Den medfølgende ZIP er udgiverens originale pakke med materialeegenskaber. Den rummer den fælles JSON-fil, enkeltfiler for prøverne, regneark og supplerende formater. Udtrækket bruger primærfilen `materialProperties/allMaterialProperties.json`. Hver observation henviser til et sted i den fil. Testen sammenholder alle værdier med enkeltfilerne i samme arkiv. Tidsserier for de 56 samlede vægge findes i en separat fil hos udgiveren. [Originalpakke](originals/materialProperties.zip) · [Udgiverens metode og beskrivelse](originals/README.md)

## Genskab dataene

Kør fra repositoryets rod med Rust og Cargo.

```sh
cargo run --locked --bin ft-materials -- collect-tampere
cargo test --locked --test thermal_rust
```

Importen bekræfter originalernes SHA-256 før udtræk. Mangler en originalfil, henter programmet filen fra udgiverens faste versionsadresse og kontrollerer de hentede bytes. Angiv `--output /sti/til/udtraek` for at give de genererede JSONL-filer en anden placering.

## NISTs målinger

NIST SRD 81 er registreret som en yderligere kilde til varmeegenskaber. NIST kræver forudgående tilladelse til kopiering og lagring af Standard Reference Data. Katalogposten linker til NISTs søgefunktion, hvor man kan se målingerne. [Kildestatus](related-sources.json) · [Søg i SRD 81](https://srdata.nist.gov/insulation/Search/DatabaseSearch) · [Udgiverens vilkår](https://www.nist.gov/srd/public-law)
