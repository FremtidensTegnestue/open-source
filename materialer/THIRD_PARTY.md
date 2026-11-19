# Kilder, kreditering og rettigheder

Projektets egen kode og dokumentation er udgivet under [MIT](../LICENSE). Det giver ikke en ny fælles licens til de kilder, som værktøjet anvender.

## Materialedata

Det fulde Parquet-snapshot og den tilsvarende SQLite-database bevarer kildebestemte licensfelter, udgiver, URL, hentetid, filkontrolsum og præcis lokation. Disse felter er oplysninger fra indsamlingen; `verified`, `unknown` og `restricted` er registrerede statusmarkeringer, ikke en ny juridisk afgørelse for en bestemt brug.

| Kilde | Kreditering og bevarede forhold |
| --- | --- |
| ÖKOBAUDAT | BMWSB / BBSR samt de enkelte dataejere og programoperatører. [Officielle vilkår](https://www.oekobaudat.de/no_cache/en/database/search.html) beskriver gratis distribution af uændrede data med kildeangivelse. Individuelle felter med afvigende/ukendt status bevares; de må ikke skjules ved en samlet MIT-etiket. |
| Danske BR18-referenceværdier | Social- og Boligstyrelsen samt de underliggende deklarationers ejere. Der blev ikke identificeret én samlet genudgivelseslicens i kildefilerne; kilde- og referenceoplysninger følger med tallene. |
| USDA Wood Handbook | U.S. Department of Agriculture, Forest Service, Forest Products Laboratory, 2021. Kapitel, tabel, betingelser og henvisninger bevares; tredjepartsbidrag er ikke blevet ommærket til projektets egen licens. |
| OpenStudio | Alliance for Sustainable Energy / U.S. Department of Energy og angivne kildeejere. [Bevaret licens](data/licenses/openstudio/LICENSE.md). |
| EnergyPlus | U.S. Department of Energy og de anførte bidragydere. [Bevaret licens](data/licenses/energyplus/LICENSE.txt). |

Datasættet bevarer værdierne og deres kontekst. Eksport til Parquet og genopbygning til SQLite omregner ikke kildeværdier og skaber ikke automatisk produktækvivalens, fælles metode eller fælles anvendelsesret. Brug den konkrete kilde og dens angivne betingelser ved videre anvendelse.

## Modelprogrammer

SolidCraft udvikles af Tangency Labs og bidragydere. BIMCraft i dette projekt er [IPedrax/BIMCraft](https://github.com/IPedrax/BIMCraft). Programmerne installeres separat og er ikke udviklet af Fremtidens Tegnestue. Kopier af deres offentlige dokumentation og CLI-hjælp ligger i `sources/programmer/` sammen med bevarede licenser og notices. Dette er dokumentationssnapshots, ikke en distribution af hele programmernes kildekode eller binære installationer.

## Vandkunsten og projektarkivet

Vandkunstens [open source-side](https://opensource.vandkunsten.com/) gav et udgangspunkt med værktøjer og projektmateriale. Katalogerne bevarer oprindelige adresser og angivelser. Det store lokale downloadarkiv, leverandørplugins, projektmodeller, originaltegninger og projektfotografier er ikke lagt ind i den almindelige Git-distribution.

Arkivet omfatter blandt andet GPL-/AGPL-undtagelser og særskilte rettigheder til tegninger, modeller, fotos og fonte. Projektets MIT-licens udvider ikke disse vilkår. Hent originale værktøjer hos deres udgiver og læs de medfølgende betingelser.

Lisbjerg-rapportens offentlige PDF indeholder vores analyse uden projektfotografiet fra originalpakken. Vores små kontrolmodeller og billeder af deres geometri er eksempler fremstillet til dette projekt.

## Tillæg i Rust-udgaven

Tampere-materialernes originaler og afledte observationer distribueres med navngivning af Antti Mikkonen og Juha Vinha under CC BY 4.0. Kildeudgave, kreditering og beskrivelse af bearbejdningen følger med materialedataene. [Tampere og ophav](data/supplements/tampere/README.md)

EPD Danmark-tillæggets kildefiler, udtrukne resultater og arbejdsdatabase hentes og oprettes lokalt. Projektet distribuerer program, kildeadresser, kontrolsummer, dækningsoplysninger og udtræksbeskrivelser. Originalernes rettigheder tilhører de respektive rettighedshavere. [Dansk kilderegister](data/supplements/epd-danmark/README.md)

Energistyrelsens regneark for individuel opvarmning angiver CC BY 4.0. BUILDs tabel over middellevetider indlæses fra Aalborg Universitet til lokalt studium eller forskning under portalens vilkår. [Udgivere, præcise udgaver og bearbejdning](docs/sources/danske-levetider.md)

Prøvningsdata, inventarlister, produktdeklarationer og producentvejledninger har særskilte vilkår. Hver kilde har egen kreditering og kontrolsum. [Faglige kilder og oprindelige filer](docs/sources/field-sources.md) · [Levetid og driftskilder](docs/sources/operations.md)
