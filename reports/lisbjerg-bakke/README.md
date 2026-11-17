# Lisbjerg Bakke — hvad kan vi beregne, og hvad mangler?

[Læs den offentlige rapport som PDF](rapport-offentlig.pdf). Analysen er udført 17. november 2026 på Vandkunstens delte ARK-/KON-modeller og seks PDF-tegningssæt med tilsammen 132 sider. Den offentlige PDF indeholder analysen uden projektfotografiet fra originalpakken.

KON giver blandt andet 75 trædæk med **354,568 m³**, 20 betondæk med **209,709 m³** og to krydsfinerdæk med **0,096 m³**. Det er BIMcrafts programberegnede, afrundede modelmængder. `Wood - C35` er kontrolleret mod originalens materialetildeling; navnet dokumenterer ikke et CLT-produkt, en træart eller en densitet.

ARK og KON holdes adskilt, da fagligt overlap og koordinater ikke er fuldt afstemt. Der leveres ingen samlet bygningsvægt eller LCA. Et særskilt, udtrykkeligt C25/30-referencescenarie for de 20 betondæk viser beregningskæden til 471.006,414 kg og 50.539,869 kg CO₂e for A1–A3 alene.

## Data, du kan læse med det samme

| Fil | Indhold |
| --- | --- |
| [summary.json](data/summary.json) | Hovedtal, modelkontrolsummer, importtab og scenarieresultat |
| [element-inventory.csv](data/element-inventory.csv) | 5.149 kildeelementer eksklusive åbninger; STEP-id, GUID, materialenavn og tilgængelige mængder |
| [missing-data.csv](data/missing-data.csv) / [JSON](data/missing-data.json) | 14 prioriterede afklaringer med ansvar og effekt |
| [material-readiness.md](data/material-readiness.md) / [kandidater](data/material-candidates.json) | Materialefamilier, mulige referencer og manglende produktdata |
| [sources.json](sources.json) | Originalernes adresser og SHA-256 |
| [validation.json](validation.json) | Kontrolstatus for rapportforløbet |

Objektantal er ikke masseprocenter eller et mål for, hvor stor en del af byggeriet der er dækket. Samlinger og delobjekter kan overlappe. Rumvolumen og åbninger er ikke materialemængder. Et manglende CLI-volumen betyder ikke, at originalens geometri mangler.

## Originaler og efterprøvelse

Originalerne findes på [Vandkunstens Lisbjerg-side](https://opensource.vandkunsten.com/07_FBABLisbjerg/) i den [delte projektpakke](https://opensource.vandkunsten.com/07_FBABLisbjerg/VK_FBABLisbjerg.zip). Modeller, originaltegninger og fotografier er ikke genudgivet som Git-filer her. `sources.json` bevarer deres individuelle identitet.

De fulde rå revisions-/parserarkiver og rapportens lokale HTML/assets ligger heller ikke i Git-pakken. De beholdes i arbejdsarkivet. De publicerede udtræk og kildehenvisninger ovenfor gør tallene læsbare uden dette arkiv; en ny udtrækning kræver originalmodellerne og den angivne værktøjsversion.

Reproduktion af mængdeudtræk sker gennem `materials.py extract MODEL.ifc --software bimcraft` med BIMcraft CLI 0.12.0. [Beregningsguiden](../../docs/CALCULATIONS.md) beskriver metoder, præcision og begrænsninger. [Det lille samlede eksempel](../../examples/integrated-workflow/README.md) er den nemmeste vej til selv at afprøve hele kæden.
