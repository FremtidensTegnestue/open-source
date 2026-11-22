# Kilder og tegninger til Byg videre på huset

## Ryesgade 30 C, 1. tv.

Den gennemførte byfornyelse af Ryesgade 30 A–C og forsøget i prøvelejligheden er beskrevet i COWIs slutrapport for EUDP-projektet fra oktober 2014. Rapporten gengiver delrapporten om prøvelejligheden i bilag A. Her bruger vi PDF’ens fortløbende sidetal, så linket lander i det rigtige dokument.

- Oprindelig ejendom, materialer og indretning før byfornyelsen. [COWI, hovedrapport, PDF-s. 17–18](https://energiforskning.dk/files/slutrapporter/64009-0233_slutrapport_inkl._delrapport2.pdf#page=17)
- Gennemførte indgreb i ejendommen, herunder inddragelse af bagtrapper i to opgange. Beskrivelsen gælder ejendommen som helhed. [COWI, hovedrapport, PDF-s. 19](https://energiforskning.dk/files/slutrapporter/64009-0233_slutrapport_inkl._delrapport2.pdf#page=19)
- Den endelige vinduesløsning i ejendommen. [COWI, hovedrapport, PDF-s. 20](https://energiforskning.dk/files/slutrapporter/64009-0233_slutrapport_inkl._delrapport2.pdf#page=20)
- Tre opholdsrum i række, to stuer en suite og en sidefløj. [COWI, bilag A, figur 1, PDF-s. 49](https://energiforskning.dk/files/slutrapporter/64009-0233_slutrapport_inkl._delrapport2.pdf#page=49)
- Bræddegulv, loftsstuk, forsøgets fire vinduesløsninger og afprøvning af ventilation og isolering. [COWI, bilag A, PDF-s. 52](https://energiforskning.dk/files/slutrapporter/64009-0233_slutrapport_inkl._delrapport2.pdf#page=52)
- Tavle 1 og 2 bygger på vores egen skematisering af de tre rumfelter og vinduesprøvernes placering. Vi har drejet planudsnittet og udeladt trapper, gang og funktionsrum. Rummenes omrids er aflæst til illustration. [COWI, bilag A, figur 4, PDF-s. 53](https://energiforskning.dk/files/slutrapporter/64009-0233_slutrapport_inkl._delrapport2.pdf#page=53)

## Værkstedsplanen og dens tre forslag

Fra tavle 3 bruges et frit tegnet udsnit med en gang og to rum. Alt foregår på samme grundplan med et indvendigt tværmål på 8.000 mm. Hver ny åbning er 1.000 mm i rå planbredde. Væggene er tegnet uden overliggere. Planerne afprøver sammenhænge mellem rum. Virkelige vægges opbygning, bæreevne, installationsføring og betydning for brand og lyd skal undersøges i den konkrete bolig. Beboernes ture med te, tasker og stole er tænkte prøver.

Kirstine Brøgger Jensens projektforslag til Birkevænget viser, hvordan den samme bolig kan læses på flere måder gennem adgang, privathed og gennemlysning. Det er en selvstændig case og en metodisk inspirationskilde. De viste Ryesgade-forhold kommer fra COWI. Bogens A, B og C er Fremtidens Tegnestues egne. [GI, Renoveringsguide, PDF-s. 109–111](https://gi.dk/media/11tjymxh/renoveringsguide.pdf#page=109)

Københavns Kommune forklarer, hvilke oplysninger der skal fremgå af før- og efterplaner ved byggeansøgning. Bogens principsnit kan bruges ved samtalen før en opmåling. [Københavns Kommune, Plantegning til byggeriet](https://www.kk.dk/borger/bolig-og-byggeri/byggetilladelse/byggetilladelse-trin-for-trin/trin-2-naar-du-laver-din-byggeansoegning/ansoegningsmateriale-og-dokumentation-til-byggeri/plantegning-til-byggeriet)

Dialogværktøjets opslag om genbrugte indvendige døre skelner mellem håndtering af bladet og afmontering af karmen. Bogens optælling omfatter de dørblade, der overflyttes i de enkelte forslag. Karmenes stand, pasning og muligheder for flytning er uafklarede. [Dialogværktøj, Genbrugte indvendige døre, PDF-s. 74](https://www.ucviden.dk/ws/files/107139883/Dialogv_rkt_j_samlet_20190917.pdf#page=74)

## Efterprøvning af tegningerne

De syv redigerbare modeller ligger i [modeller](modeller/). Alle er oprettet, eksporteret og inspiceret med SolidCraft CLI. Tavlerne er tegnet som projektioner af modellernes eksporterede flader. Ruter, farver, målestok og tekst er redaktionelle anmærkninger.

| Tavler | Modeller | Kontrol |
| --- | --- | --- |
| 1–2 | rumfoelge.sc | Tre lukkede rumlegemer. Rumfølgen, det midterste rums knæk, gadens to vinduer og prøvevinduet mod gården er sammenholdt med figur 4. |
| 3–9, 12–14 | basis.sc, A.sc, B.sc, C.sc | Grundplanens 19 legemer og varianternes henholdsvis 21, 20 og 19 legemer er lukkede. Åbningernes koordinater og de navngivne dørblades mål er sammenholdt mellem før og efter. |
| 10 | doersaet.sc | Fire lukkede legemer. Skematisk adskilt blad og tre karmstykker. Ingen påstand om pasning eller oprindelige Ryesgade-profiler. |
| 11 | gulvspor.sc | Tre lukkede legemer. Det nye mellemfelt ligger mellem gulvstykkerne. Dets valgte mål gælder bogens model. |

| Forslag | Ny åbning | Lukket åbning | Blad flyttet fra før-planen | Særskilt nyt blad | Gammelt blad udtaget uden ny placering |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 1 | 1 | 1 | 0 | 0 |
| B | 1 | 1 | 0 | 1 | 1 |
| C | 1 | 0 | 1 | 0 | 0 |

Bladet i gangdøren til stue 1 bliver siddende i alle tre forslag. I A ses den nye passage i skillevæggen 400–1.400 mm fra gangvæggens inderside. Den gamle lå 2.300–3.300 mm fra samme linje. I B og C er det i stedet gangvæggen ved rum 2, der får en åbning. Alle tre anvender samme afgrænsning af udsnittet. Møbelplacering og faktiske passagebredder skal afprøves i boligen.

## Opslag med videns-CLI

- `vidensbank-soeg --titler 'Erfaringer fra prøvelejlighed Ryesgade 30C 1tv'` fandt EUDP-projektets hovedrapport inklusive bilag A. Den er anvendt som fælles kilde til før- og efterforhold og forsøgsplanen.
- `vidensbank-soeg --tekst 'transformation bolig lejlighed rum opdeling genbrug døre eksisterende plan'` fandt blandt andet GI’s renoveringsguide på PDF-s. 111. De omkringliggende sider blev læst sammen med planerne for Birkevænget.
