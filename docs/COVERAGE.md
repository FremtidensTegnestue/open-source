# Dækning af første materialedatabase

Aktuelle tillæg i v0.2 omfatter Tampere og en særskilt lokal indsamling fra EPD Danmark. Denne side dokumenterer de fire grunddatasæt fra 17. november. [Se de samlede optællinger](../README.md#tallene-følger-med)

Den aktuelle maskinlæsbare optælling findes i `data/catalog.json`. Første samlede indsamling, 17. november 2026:

| Datasæt | Kildebestemte poster | Numeriske observationer | Hvad det dækker |
| --- | ---: | ---: | --- |
| ÖKOBAUDAT | 7.067 | 1.962.722 | Publicerede miljøindikatorer, energi-/ressource-/affaldsdata, flowegenskaber og tilgængelige strukturerede materialeegenskaber |
| OpenStudio / EnergyPlus | 3.183 | 15.127 | Termiske og fysiske egenskaber, glasoptik, fugtmodeller og kurver, lag og solafskærmning |
| USDA Wood Handbook | 325 | 5.038 | Træarters fugt, svind, dimensionsændringskoefficienter, mekanik, varmeledning og varmekapacitet |
| Danske BR18-tabeller 7–11 | 586 | 2.695 | Klima- og massefaktorer, energi, brændstoffer, transport, konstruktioner og affaldsbehandling |
| **I alt** | **11.161** | **1.985.582** | **Fire dokumenterede indsamlinger** |

## Originaler

7.135 registrerede kildefiler er bevaret og kontrolleret med SHA-256. De samlede filer under `data/raw/` fylder ca. 706 MB inklusive afledt tekst og HTTP-metadata. Miljødataenes originaler er de publicerede maskinlæsbare JSON-datasæt. 4.685 adresser til deres bilag er registreret, men bilagene er ikke alle downloadet. Den danske indsamling har derimod hentet alle 24 forskellige PDF'er, der er direkte linket fra tabel 7. Hele USDA Wood Handbook er gemt, mens udvalgte dokumenterede tabeller fra kapitlerne 4, 5 og 13 er struktureret.

## Sådan skal antal forstås

Et datasæt, et produkt, en materialetype og en biologisk træart er ikke samme identitetsniveau. Poster fra forskellige kilder er bevaret særskilt. Optællingen er derfor ikke et løfte om 11.161 unikke materialer. Nulværdier er eksplicitte kildeværdier og tæller som observationer; manglende eller ikke-deklarerede værdier erstattes ikke af nul.

Miljødatapunkter er hver en værdi for en bestemt indikator, metode, referenceenhed, modul og eventuelle scenariebetingelser. En egenskabsværdi fra et simuleringsbibliotek er ikke automatisk en deklareret egenskab for en bestemt dansk byggevare.

## Datakvalitet og usikkerheder

- Originale enheder og kildebetingelser bevares. Originaldatabasen er ikke masseomregnet til SI eller metodeharmoniseret; beregningsmotoren understøtter eksplicitte konverteringer ved brug.
- USDA-trætabellerne beskriver blandt andet små fejlfrie prøver; de er ikke automatisk dimensioneringsværdier for styrkesorteret konstruktionstræ.
- OpenStudio har imperiale enheder; fire AirGap-værdier har eksplicit uklar kildeenhed og er markeret.
- Tre sorterings-ID'er gentages i den officielle BR18-materialetabel; rækkeafgrænsede ID'er bevarer alle forekomster.
- En stor del af de tekniske poster er simuleringsinput. Original kontekst og type følger med hvert punkt.
- Historiske/udløbne miljødeklarationer bevares med deres gyldighedsoplysninger.
- Materialefamilier er søgegrupper, ikke en certificeret klassifikation eller automatisk ækvivalens mellem produkter.

Brandklassifikationer, akustik, kemiske emissioner, produktlevetider, priser og øvrige visionsegenskaber har endnu ikke en samlet struktureret dækning. Nogle kan forekomme i originalerne uden at være udtrukket. Dette er et dokumenteret datagrundlag, som kan udvides bredt, og ingen materialefamilie er en vedtaget permanent afgrænsning.

## Rettigheder

Licensstatus findes pr. kilde og i dokumentationen for hvert datasæt. ÖKOBAUDATs vilkår for uændrede data er gemt sammen med individuelle deklarationers licensfelter. Ukendte eller afvigende felter bevares som sådan. Der er ikke tildelt en ny fælles MIT- eller CC-licens til samlingen. ECO SMDP er undersøgt, men ikke bulk-importeret på grund af de fundne API-/videreudgivelsesvilkår.

## Leveret funktion og næste integrationsbehov

Den samlede SQLite-database, reproducerbare collectors, kildedokumentation og et JSON-CLI til søgning/opslag/kontrol er leveret. Der er siden leveret read-only modeladaptere til BIMcraft/Solidcraft, enhedskonvertering, masse-/modulvise klima-/træfugtberegninger og en repository-agent-skill. Ti faktiske modelcases er dokumenteret i [kontrolrapporten](VALIDATION.md). Materialematch kræver fortsat eksplicit datavalg; kandidatforslag er ikke automatisk produktækvivalens.
