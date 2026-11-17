# Ordliste

Ordene her bruges i [introduktionen](KOM-GODT-I-GANG.md), kommandoerne og beregningsrapporterne.

| Ord | Betydning i dette projekt |
| --- | --- |
| **Repository / repo** | Projektets samlede mappe med kode, dokumentation og eksempler. Du kan læse den på nettet eller hente en lokal kopi. |
| **Projektrod** | Den øverste projektmappe, som indeholder `materials.py`. Kommandoerne i guiderne køres herfra. |
| **AI-agent** | Et AI-program, der kan bruge værktøjer, eksempelvis læse filer og køre kommandoer. Agentens faktiske adgang afhænger af det program og den opsætning, du bruger. |
| **Skill** | En vejledning til en agent om en bestemt arbejdsgang. Projektets skill ligger i `.agents/skills/material-model-assessment/SKILL.md`. Den giver ikke i sig selv adgang til filer eller programmer. |
| **CLI / terminal** | CLI betyder kommandolinjegrænseflade. I en terminal skriver du en kommando og får et tekstsvar. En agent kan bruge samme grænseflade. |
| **MCP** | Model Context Protocol: en standard, som et agentprogram kan bruge til at forbinde sig med andre værktøjer. SolidCraft og BIMCraft har MCP-adgang. Arbejdsgangene her kan også køre gennem deres CLI; en MCP-forbindelse bliver ikke automatisk oprettet ved at hente dette projekt. |
| **Lokalt Python-miljø / venv** | En mappe med projektets eget Python-miljø. `.venv` er et almindeligt navn til den. |
| **JSON** | Et tekstformat med faste feltnavne og værdier. Her bruges det til beregningsinput, bindinger og rapporter. |
| **SQLite** | En database samlet i én fil. Hele materialedatabasen ligger i `data/materials.sqlite`, når du har gendannet den fra de medfølgende Parquet-filer. Kommandoerne læser denne fil ved opslag og beregning. |
| **Parquet** | Et format, der gemmer tabeldata kolonnevis og er velegnet til større analyser. `data/parquet/` indeholder alle materialedatabasens tabeller i kompakt form. Projektets materiale-CLI bruger den gendannede SQLite-fil. |
| **Release / udgivelsesfiler** | En bestemt version af projektet og de tilhørende downloadfiler. En færdig SQLite-database kan valgfrit hentes fra udgivelsen i stedet for at gendanne den lokalt. |
| **Zstandard / .zst** | Komprimering, som gør databasefilen mindre at hente. Downloadscriptet pakker den ud til en almindelig SQLite-fil. |
| **CAD / Solidcraft** | CAD er geometrisk modellering. I dette projekt bruges Solidcraft til CAD og til at hente målte volumener fra lukkede legemer. |
| **BIM / BIMcraft** | BIM kobler bygningsgeometri med strukturerede oplysninger om elementer og materialer. BIMcraft er et af de programmer, som værktøjet kan læse modeller fra. |
| **IFC** | Et udvekslingsformat til bygningsmodeller. Import kan ændre eller udelade indhold; importerede mængder og advarsler skal gennemgås. |
| **GLB / mesh** | GLB kan indeholde en model som trekantsflader, også kaldet et mesh. Overførslen kan bevare geometrien uden at bevare CAD-parametre og konstruktionshistorik. En beregnelig volumen kræver blandt andet en lukket geometri. |
| **Modeladapter / udtræk** | Koden, der spørger Solidcraft eller BIMcraft om en model og omsætter svaret til en fælles struktur. Udtræk læser modellen uden at gemme ændringer i den. |
| **Mængde** | Eksempelvis volumen i m³, masse i kg eller et bestemt referenceareal i m². Et legemes totale overflade er ikke automatisk det areal, en klimadeklaration gælder for. |
| **Densitet / massefylde** | Masse pr. volumen, typisk kg/m³. Værktøjet beregner masse som volumen × densitet. kg/m² er arealvægt og kan ikke bruges som densitet. |
| **Materialepost** | En kildebestemt post for et materiale, produkt eller en konstruktion. To lignende navne fra forskellige kilder beviser ikke, at posterne beskriver samme produkt. |
| **Observation** | En bestemt kildeoplysning om en egenskab, eksempelvis densitet ved et angivet fugtindhold eller et klimatal for et bestemt modul. Den har sit eget ID, enhed og kildehenvisning. |
| **Binding** | En JSON-fil, der forbinder et modelelement med en bestemt materialepost og valgte observationer. Filen angiver også begrundelse og modelversion. |
| **Reference / referencescenarie** | Et tydeligt beskrevet datavalg til en sammenligning, eksempelvis generisk beton. Det dokumenterer ikke i sig selv, hvilket produkt der bliver leveret eller bygget med. |
| **Deklareret mængde / referencegrundlag** | Den mængde, en kildeværdi gælder for, eksempelvis 1 m³, 1 ton eller 1.000 kg. Grundlaget skal være kendt, før værdien kan skaleres til modellens mængde. |
| **EPD** | Environmental Product Declaration: en miljøvaredeklaration med oplysninger om et produkt og dets miljøpåvirkninger under angivne betingelser. Relevans, metode og mængdegrundlag skal vurderes før brug. |
| **GWP / kg CO₂e** | GWP er en indikator for bidrag til global opvarmning. kg CO₂e udtrykker drivhusgassers påvirkning som CO₂-ækvivalenter. Det er ikke materialets masse. |
| **A1–A3 / modul D** | A1–A3 dækker produktets fremstillingsfase. Modul D beskriver potentielle gevinster og belastninger uden for systemgrænsen og holdes særskilt. Værktøjet bevarer kildens modulopdeling. |
| **LCA** | Livscyklusvurdering. Beregningerne her kan levere udvalgte bidrag; en komplet bygnings-LCA kræver et samlet grundlag for blandt andet bygningsdele, livscyklusfaser og scenarier. |
| **Træfugt / radial / tangential** | Træfugt er vandindhold i træ i forhold til dets tørmasse. Radial er på tværs af årringene, tangential langs årringene. Bevægelseskoefficienten afhænger blandt andet af art og retning. Træfugt er ikke luftens relative fugtighed. |
| **Checksum / SHA-256** | Et digitalt fingeraftryk af en fil. Det bruges til at opdage ændringer i modeller og kilder. Det beviser filidentitet, ikke faglig korrekthed. |
| **`ok` / `partial` / `unresolved`** | Rapportstatus: gennemført inden for det angivne grundlag, delvist beregnet eller uafklaret. En gennemført beregning kræver stadig gennemgang af kilder, antagelser og advarsler. |

De præcise metoder, kildekrav og begrænsninger står i [beregningsguiden](CALCULATIONS.md) og [databaseguiden](DATABASE.md).
