# Kom godt i gang

Her kan du undersøge materialers vægt, udvalgte klimabidrag og træets fugtbevægelse med sporbare kilder. Du kan begynde med at læse et færdigt eksempel. Når du vil videre, kan en AI-agent hjælpe med filerne, eller du kan selv bruge kommandoerne.

Et beregnet klimabidrag gælder den valgte mængde, kilde og livscyklusfase. Det er ikke i sig selv en komplet bygnings-LCA eller dokumentation for, at et projekt opfylder BR18.

## Vælg en vej ind

| Du vil … | Start her | Du behøver |
| --- | --- | --- |
| Se, hvad der allerede virker | [1. Læs et eksempel](#1-læs-et-eksempel-uden-installation) | En browser |
| Have hjælp til din opgave | [2. Arbejd med en AI-agent](#2-arbejd-med-en-ai-agent) | Projektmappen og en agent med adgang til lokale filer og en terminal |
| Køre værktøjet selv | [3. Prøv kommandoerne](#3-prøv-kommandoerne-selv) | Python 3.11 eller nyere; modeludtræk kræver også det relevante modelprogram |

Ukendte ord er forklaret i [ordlisten](ORDLISTE.md).

## 1. Læs et eksempel uden installation

Åbn [det samlede model- og beregningseksempel](../examples/integrated-workflow/README.md). Du kan læse teksten og se modellen direkte på repositoryets hjemmeside.

Eksemplet følger en betonplade med en udsparing og to stålskinner. Pladens tykkelse ændres fra 100 til 120 mm. Med de valgte generiske materialereferencer stiger den samlede masse fra cirka 336 til 401 kg. Klimabidraget i A1–A3 stiger fra cirka 55,3 til 62,2 kg CO₂e. Det er et kontrolleret referencescenarie med tre dele.

Geometrien oprettes i Solidcraft og overføres til BIMcraft. Begge programmer leverer mængder til beregningerne. Returgeometrien kontrolleres særskilt; CAD-modellens parametre og historik følger ikke med gennem GLB-formatet.

Se især:

- [Resultat og før/efter](../examples/integrated-workflow/README.md#modellen-og-resultatet): den læsbare forklaring.
- [Materialekortet](../examples/integrated-workflow/material-manifest.json): de valgte referencer.
- [Grundmodellens beregning](../examples/integrated-workflow/base/solid-assessment.json): tal, enheder og kildehenvisninger i JSON.
- [Fugt-eksemplet](../examples/reports/solidcraft-moisture-assessment.json): et 232 mm bredt træemne, hvis beregnede bevægelse er cirka 1,71 mm ved ændring fra 8 til 11 % træfugt under de angivne arts- og retningsforudsætninger.

JSON er tekst med faste feltnavne. I en beregningsrapport kan du begynde med `status`, `warnings` og hvert elements `calculations`. Kildehenvisninger står under beregningernes input. `partial` betyder, at noget er uafklaret; manglende værdier er ikke nul.

## 2. Arbejd med en AI-agent

En AI-agent er et program, som både kan forstå din beskrivelse og bruge værktøjer. I denne arbejdsgang læser den lokale filer og kører de samme kommandoer, som du selv kan køre. En almindelig chat kan forklare indsat tekst, men har ikke automatisk adgang til din mappe eller dine modelprogrammer.

### Hent mappen og brug den medfølgende skill

Hent eller klon projektet som beskrevet i [forsiden](../README.md). Åbn hele projektmappen i dit agentprogram. Rodmappen er den mappe, som indeholder `materials.py`.

Der følger en lokal skill med: [material-model-assessment](../.agents/skills/material-model-assessment/SKILL.md). En skill er en vejledning til agenten. Filen ligger allerede i `.agents/skills/material-model-assessment/SKILL.md`; den er ikke dermed installeret i alle dine agentprogrammer. Automatisk opdagelse afhænger af programmet. Du kan bruge den manuelt ved at give agenten denne besked:

> Arbejd i denne projektmappe. Læs README.md, docs/KOM-GODT-I-GANG.md og .agents/skills/material-model-assessment/SKILL.md, og følg skillens arbejdsgang. Undersøg først, hvilke værktøjer der er tilgængelige. Brug projektets lokale Python-miljø og den fulde database i data/materials.sqlite; gendan databasen med scripts/build_database.py fra projektets Parquet-filer, hvis den mangler. Begynd med det gemte eksempel og forklar resultatet på almindeligt dansk. Vis kilder, forudsætninger og mangler.

På den måde aktiverer du vejledningen i det aktuelle projekt uden at skulle ændre en global agentopsætning. Python skal være tilgængelig for at køre materialeværktøjet; læsning af de gemte eksempler kræver ingen installation. Nye modeludtræk kræver også `solidcraft-cli` eller `bimcraft-cli` på maskinen. Programmerne er [SolidCraft](https://solidcraft.io/download/) og [BIMCraft fra IPedrax](https://github.com/IPedrax/BIMCraft/releases/tag/v0.12.0). Eksemplerne er afprøvet med SolidCraft CLI 0.44.0 og BIMCraft CLI 0.12.0.

### Spørgsmål, du kan kopiere

**Forstå et resultat:**

> Forklar examples/integrated-workflow/README.md og den tilhørende beregningsrapport. Hvilke tre dele er med? Hvor kommer densitet og klimatal fra? Hvad er beregnet, og hvad mangler for at beskrive en rigtig bygnings samlede klimaaftryk?

**Vægt fra din model:**

> Undersøg min model [indsæt filsti]. Brug Solidcraft eller BIMcraft til mængdeudtræk. Find mulige datakilder til densitet og vis mig kilden og dens forudsætninger, før du bruger den. Beregn derefter massen for de dele, der har et dokumenteret grundlag. Vis uafklarede dele særskilt og gem rapporten i output/.

**Sammenlign klimabidrag:**

> Sammenlign to tykkelser af [bygningsdel/materiale] i min model [indsæt filsti]. Afgræns sammenligningen til A1–A3 med samme indikator og kildegrundlag. Gør eventuelle generiske materialevalg til tydelige referencescenarier. Vis mængder, kildeværdier og forskellen mellem varianterne.

**Træets fugtbevægelse:**

> Undersøg fugtbevægelsen for et [træart]-emne med bredden [mm], fra [start] til [slut] procent træfugt. Afklar radial eller tangential retning og emnets orientering. Brug en dokumenteret koefficient inden for dens gyldighedsinterval, og fortæl hvilke oplysninger der mangler.

Erstat teksten i kantede parenteser med din egen opgave. Træfugt i disse spørgsmål er vandindhold i træet, ikke luftens relative fugtighed.

### Sådan bliver et tal til

Arbejdsgangen er: **model → mængdeudtræk → kildevalg → binding → beregning → gennemgang**.

1. Agenten læser modellens elementer, mængder og advarsler.
2. Den søger efter mulige materialer. Et enslydende navn er kun et forslag.
3. Du og agenten afklarer materiale, kilde, enheder og betingelser. Et ubekræftet produktvalg kan i stedet beskrives som et referencescenarie.
4. Agenten gemmer valget i en bindingsfil, som peger på bestemte kildeobservationer og den konkrete modelversion.
5. Værktøjet beregner de understøttede bidrag. Agenten forklarer resultat, kilder og mangler.

**Vægt** kræver volumen og densitet. **Klima** kræver en valgt GWP-observation, et modul og et deklareret mængdegrundlag. **Fugtbevægelse** kræver træart, materialeretning, emnemål og start-/slutfugt. En model med en materialefarve eller navnet “træ” indeholder ikke alle disse oplysninger.

## 3. Prøv kommandoerne selv

### Åbn en ny lokal kopi

Hent ZIP-filen eller klon repositoryet fra dets `Code`-menu, og åbn en terminal i mappen med `materials.py`. Bevar mappestrukturen, også den skjulte `.agents`-mappe. Alle materialedata følger med som Parquet-filer i `data/parquet/`. De gendannes til en SQLite-database i næste trin; regn med cirka 9 GB ledig diskplads.

Brug Python 3.11 eller nyere. Et lokalt Python-miljø holder projektet adskilt fra andre Python-projekter.

**macOS/Linux:**

```sh
python3 --version
python3 -m venv .venv
. .venv/bin/activate
```

**Windows PowerShell, her med Python 3.11:**

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Har du en nyere Python-version på Windows, vælger du den i stedet for `-3.11`. Hvis PowerShell afviser aktivering, kan du bruge `.\.venv\Scripts\python.exe` i stedet for `python` i kommandoerne nedenfor.

### Gendan hele materialedatabasen

```sh
python -m pip install -r requirements.txt
python scripts/build_database.py
python materials.py verify --database-only
```

De medfølgende Parquet-filer fylder cirka 91 MB og rummer alle tabeller og omkring 1,99 millioner observationer. Scriptet gendanner dem som hele `data/materials.sqlite`, der fylder cirka 8,8 GB. Det kræver ingen ny indsamling og ingen netadgang til data. Installation af Python-pakker kan kræve internet første gang. Databasekontrollen ovenfor kontrollerer SQLite-integritet og relationer og kræver ingen originalfiler.

| Filtype | Hvad den bruges til |
| --- | --- |
| **SQLite** | Den fulde arbejdsdatabase til projektets kommandoer, AI-agenter og modelberegninger. Den gendannes lokalt fra Parquet-filerne. |
| **Parquet** | Den kompakte udgave af alle tabeller, som følger med projektet i `data/parquet/`. Den kan også bruges direkte i dataanalyseprogrammer. Materialeværktøjets CLI læser SQLite. |
| **Originalfiler** | Kildernes Excel-, PDF- og andre filer til efterprøvelse. De hentes særskilt efter behov. Kildeadresser, enheder og betingelser bevares i databasen. |

Som alternativ til lokal gendannelse kan `python scripts/download_data.py` hente en færdig SQLite-database fra udgivelsen, cirka 187 MB komprimeret. Du skal kun vælge én af de to veje.

`requirements.txt` installerer blandt andet værktøjerne til Parquet og udpakning. Selve materiale-CLI'et bruger Pythons standardbibliotek. De enkelte datakilders rettigheder fremgår af deres metadata; en åben softwarelicens giver ikke automatisk samme licens til alle data.

### Prøv en enhed og find en kilde

Kør først en enhedskonvertering. Den kræver ingen database eller modelprogrammer:

```sh
python materials.py normalize --value 1 --unit 'lb/ft^3' --dimension density
```

Svaret indeholder cirka `16.01846` i `kg/m3`. Prøv derefter materialeopslag i den fulde database:

```sh
python materials.py stats
python materials.py search beton --limit 5
python materials.py show br18:t7:B1433:row25
python materials.py observations --material br18:t7:B1433:row25 --limit 10
```

`show` viser den valgte materialepost. `observations` viser egenskaberne og deres grundlag. Værdier fra andre produkter, enheder eller fugtforhold må ikke automatisk erstatte hinanden. De konkrete ID'er kommer fra søgeresultaterne; ID'et ovenfor er betonreferencen i det samlede eksempel.

### Beregn et klimabidrag uden en model

Dette eksempel bruger en kendt mængde på 500 kg og én udvalgt ÖKOBAUDAT-observation. Der kræves ingen CAD- eller BIM-installation:

```sh
python materials.py calculate examples/requests/environmental-1000kg.json --out output/klimabidrag-500kg.json
```

Åbn `output/klimabidrag-500kg.json`. Kildens grundlag er 1.000 kg; inputmængden er 500 kg. Det giver 429,5 kg CO₂e for netop den valgte indikator i modul A1. Filnavnets “1000kg” beskriver kildens grundlag. Resultatet omfatter kun dette modul.

### Hent originalkilder efter behov

Databasen bevarer kildeadresser og filfingeraftryk. Vil du også læse originalerne til de medfølgende beregningseksempler lokalt, kører du:

```sh
python scripts/fetch_sources.py --demo
```

`--demo` betyder her kun, at du henter originalfilerne til eksemplerne; SQLite-databasen indeholder stadig alle observationer. Det er også disse originalfiler, det samlede eksempels uafhængige kontrol læser. Vil du efterprøve alle originalfiler, henter du dem med `--all` og kører derefter `python materials.py verify`. Se [databaseguiden](DATABASE.md) for omfang og kildekontrol.

### Beregn den gemte Solidcraft-model

Dette trin kræver en installeret `solidcraft-cli`. Kommandoen bruger den medfølgende binding til netop grundmodellens materialer og modelversion:

```sh
python materials.py assess examples/integrated-workflow/base/model.sc --software solidcraft --bindings examples/integrated-workflow/base/solid-bindings.json --out output/min-foerste-beregning.json
```

Åbn `output/min-foerste-beregning.json` bagefter. Værktøjet opretter outputmappen. Resultatet indeholder beregninger for de enkelte dele og de anvendte kilder. En ændret model kræver en gennemgået, ny binding; genbrug af den gamle afvises.

Materialeværktøjets svar er JSON. `--out` gemmer en rapport som JSON. Afslutningskode 0 betyder gennemført, 1 betyder fejl, og 2 betyder et delvist eller uafklaret resultat. Læs altid rapportens status og advarsler sammen med tallene.

Fortsæt i [beregningsguiden](CALCULATIONS.md), når du vil lave dine egne bindinger, bruge BIMcraft eller beregne ud fra en kendt mængde uden en model. [Kontrolrapporten](VALIDATION.md) viser, hvad der er afprøvet, og hvilke begrænsninger der er kendt.
