# Eget arbejde, mangler og nødvendige kontroller

Vi udfører selv de opgaver, som grundlag, metode, kompetencer og regler tillader. En enkel arbejdsoversigt viser resten med næste handling og ansvarlig rolle. Den skelner mellem vores næste arbejde, faglig kontrol, formel godkendelse/erklæring og uafklaret ansvar/krav. Uafklaret betyder ikke automatisk en opgave til andre.

Fra mappen `materialer`, med Python 3.10 eller nyere:

```sh
python3 work_overview.py examples/work-overview/arbejdsliste.json --out /tmp/arbejdsoversigt.html --check
python3 work_overview.py examples/work-overview/arbejdsliste.json --serve
```

Den sidste kommando viser en lokal browseradresse. Visningen læser registreringen og kontrollerer de udtrykkeligt bundne filer cirka hvert andet sekund, mens forbindelsen er aktiv. Den skriver ikke til modellen eller registreringen. Fejl i forbindelse eller registrering markeres i visningen. Den gemte HTML-fil er et øjebliksbillede og genkontrollerer ikke sig selv. `--check` returnerer 1 ved ændret/manglende filgrundlag; åbne arbejdsopgaver er tilladt.

Eksemplet er anonymt og fiktivt. Det indeholder ingen byggetilladelse, faktisk projektspecifik fagkontrol eller personunderskrift. **Det er en separat oversigt, ikke et integreret SolidCraft-panel.**

Arbejdsoversigten kan nu også tilknyttes **den eksisterende lokale facadevisning**, så den følger materiale-/klimaregnskabet i samme side. Projekt-ID, filsti og projektbetegnelse vælges udtrykkeligt; listen genkontrolleres uafhængigt af CAD-revisionen. [Tilknytning og afgrænsning](../facade/README.md#arbejde-og-nødvendig-kontrol-i-samme-visning). Dette installerer stadig ikke et native panel i SolidCraft.

## Ved hvert afsluttet arbejdstrin

1. Registrér det faktisk udførte arbejde og de nye mangler i projektets egen JSON-fil. Bevar faste post-ID'er og præcist omfang. Generér ikke en ny liste, som glemmer eksisterende åbne punkter.
2. Begrund arbejdsfordeling og krav. `work_by` er `us`, `specialist` eller `undecided`; `requirement` er `work`, `technical_review`, `formal_approval` eller `clarify`. Rollefeltet er ingen bestilling eller udpegning af en faktisk person.
3. Bind poster til relevante input, modeller, metoder og bilag med filsti og SHA256. Registrér de relevante afhængigheder eksplicit; programmet opdager ikke automatisk alle sammenhænge eller læser betydningen af en PDF. Gem projektmateriale lokalt.
4. Brug `open` eller `prepared`, indtil det angivne omfang faktisk er afsluttet. `completed` kræver `completion` med `by`, ISO-dato, præcis `reference`, bilags-ID'er i `evidence` og den aktuelle `context_key(registry, item)` fra Python-modulet. Bilag skal indgå i postens kilder. Selve registreringen autentificerer ikke en underskrift eller en persons kompetence.
5. Kontrollér og gendan oversigten. Ved ændrede bundne filer eller ændret opgaveomfang/rolle vises »Grundlag ændret · genvurder«. Et nyt filhash alene genvaliderer ikke en gammel afslutning. Undersøg ændringen, udfør den nødvendige kontrol og registrér derefter et nyt grundlag og faktisk afslutning.

Først når konkret klassifikation og krav er afklaret, oprettes de nødvendige erklærings-/godkendelsesposter med korrekt omfang og ansvar. At den gruppe er tom, betyder ikke, at et byggeri ingen myndighedskrav har. [Ingeniørydelser og dansk dokumentationsgrundlag](../../docs/ENGINEERING-SCOPE-DK.md) giver kontekst; gældende krav og faktiske kompetencer skal afklares for hver sag.

DfD er et frivilligt tilvalg. Der er ingen automatisk ekstern bestilling, samlet godkendelsesstatus eller færdigprocent. Eksisterende beregningsforløbs egne friskhedskontroller skal stadig køres; en filbinding erstatter dem ikke.

Kontrol:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_work_overview.py' -v
```
