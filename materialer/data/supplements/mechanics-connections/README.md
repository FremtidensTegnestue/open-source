# Målt bæreevne i træsamlinger med skruer

Samlingen indeholder 79 enkeltforsøg med træskruer. I den ene serie blev en skrue trukket ud af et stykke gran. I den anden blev en samling mellem en CLT-væg og en træbjælke belastet sideværts. Hver post henviser til en enkelt række i en offentliggjort forsøgstabel. Der er ingen målinger af gentagen afmontering og genmontage i disse to udtræk.

| Forsøg | Antal | Kraft | Hvad værdien gælder for |
|---|---:|---:|---|
| Kvasistatisk udtræk i gran | 31 | 2.003–5.641 N | Én skrue langs skrueaksen, 45° til træets fiberretning |
| CLT til konstruktionstræ, monoton belastning | 24 | 18,6–52,3 kN | Den samlede spidskraft for en forbindelse med to eller fire skruer |
| CLT til konstruktionstræ, vendende cyklisk belastning | 24 | 10,4–50,2 kN | Den samlede spidskraft for en tilsvarende forbindelse under den cykliske protokol |

**Udtræk i gran.** Niebuhr og Sieder prøvede fuldgevindsskruer på 6 × 120 mm i ovntørret, fejlfrit grantræ (*Picea abies*). I 15 prøver havde gevindet 28 mm effektiv forankring, i de øvrige 16 havde det 58 mm. Spidsen stak 7 mm ud på bagsiden, så hver måling vedrører selve gevindet. Den publicerede prøvebetegnelse, densitet, belastningsretning, forankringslængde og forsøgsbetingelser følger med hver måling. Tallene er fundet i tabel 3 og kontrolleret mod både forlagets tabelvisning og originalens PDF. [Niebuhr og Sieder, originalartikel](https://doi.org/10.1007/s00107-025-02205-3) · [De 31 målinger i tabel 3](https://link.springer.com/article/10.1007/s00107-025-02205-3/tables/3)

**Samlingen mellem træ og CLT.** Eini m.fl. prøvede skruer med en diameter på 8 eller 10 mm. Der sad to 160 mm delgevindsskruer i 90° eller to 240 mm fuldgevindsskruer i 45°. De blandede samlinger havde to af hver slags. Vinklen angår fibrene i konstruktionstræet. Belastningen var parallel med fibrene. CLT-panelet havde fem lag, en tykkelse på 175 mm og amerikansk E1-klassifikation. Den registrerede spidskraft spændte fra 10,4 til 52,3 kN på tværs af alle 48 samlinger. Målingen kan afhænge af, hvordan flere skruer deler last, og om træet flækker. [Eini m.fl., forsøgsopstilling og tabel 3–4](https://www.mdpi.com/2075-5309/12/7/1018)

Tre samlinger flækkede ifølge tabelfodnote 1. Forskerne udelod dem fra deres gruppegennemsnit. De enkelte målinger er bevaret med `failure_mode` og `authors_excluded_from_group_mean`. Forskerne øgede skruernes afstand og endekantafstand under programmet. Ændringen er beskrevet i hver post med den usikkerhed om tidspunktet, som gælder for den enkelte prøve. Prøvenummeret for CLT-samlingerne angiver rækkefølgen inden for den publicerede tabelgruppe. [Eini m.fl., originale tabeller og fodnoter](https://mdpi-res.com/d_attachment/buildings/buildings-12-01018/article_deploy/buildings-12-01018.xml)

## Læs data med en agent

Feltet hedder `fastener_capacity`. Læs `conditions.scope`, `conditions.fastener_count`, `value`, `unit` og `source_locator` sammen. En kraft i N ved `single tested fastener` beskriver det individuelle udtræksforsøg. En kraft i kN ved `whole tested CLT-to-lumber connection` gælder for hele den beskrevne samling. `conditions.fastener_groups` angiver antallet, længden, diameteren, gevindtypen og vinklen for hver gruppe i samlingen. `design_value` er falsk for alle 79 resultater. En projekteret eller genbrugt samling kræver sit eget grundlag for træets tilstand, skruegeometri, afstande, last og sikkerhed.

`originals/` indeholder Springers PDF og MDPI’s udgiver-XML. `sources.jsonl` angiver forfattere, DOI, downloadadresse, licens, SHA-256 og filstørrelse. Begge artikler er publiceret under Creative Commons Navngivelse 4.0. Udtrækket organiserer forfatternes måletal og tilføjer forsøgsbetingelser fra deres metodeafsnit. [Springers original](https://link.springer.com/content/pdf/10.1007/s00107-025-02205-3.pdf) · [MDPI’s original](https://mdpi-res.com/d_attachment/buildings/buildings-12-01018/article_deploy/buildings-12-01018.xml) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
