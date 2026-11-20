# Mekaniske forsøg på murværk, sten, jord og isolering

55 prøvegrupper, murfelter og opbygninger giver 177 tal. Et opslag returnerer kildens tabel og række, enhed og forsøgsbetingelser. Originalartiklerne ligger i `originals/` og er registreret med SHA-256 og licens. [Kilderegister](sources.jsonl)

| Hvad blev prøvet? | Hvilke oplysninger findes? | Original |
| --- | --- | --- |
| Fem bjergarter | Tør og vandmættet densitet, E, Poissons tal, tryk og spaltetræk i tabel 1 | [Wang m.fl.](https://doi.org/10.1038/s41598-023-46444-x) |
| Stampet jord | Lag på 60 eller 120 mm, én eller seks måneders tørring, middelværdier og spredning i tabel 1. Forfatterne vurderer, at målemetoden kan undervurdere E | [Shrestha m.fl.](https://doi.org/10.3390/buildings10030057) |
| Ti historiske murfelter i Toscana | Stivhed og tilgængelige trykresultater fra forsøg med flade donkrafte direkte i de eksisterende mure, tabel 4–5 | [Boschi m.fl.](https://doi.org/10.3390/heritage4010014) |
| Porebeton | Blokkenes densitet og trykstyrke i tabel 2. Murværkets trykprøver med to typer mørtelfuge, E og Poissons tal i tabel 4 og forskydningsprøver i tabel 5 | [Li m.fl.](https://doi.org/10.3390/ma13071680) |
| Hampbaseret isolering | Forskellige blandingers cylindertryk, E fra trykforsøg, spaltetræk og densitet i tabel 3. Geometri og prøvningshastighed findes i afsnittet om forsøgsmetoder | [Abdellatef m.fl.](https://doi.org/10.3390/ma13215000) |
| Gipsplade, karton, stenuld og sandwichplader | Bestanddelenes egenskaber i tabel 3, opbygningernes styrke, brudenergi og bøjningsmodul i tabel 4. Tabel 6 giver stenuldens kompressionsmodul i to retninger. Papirets tvetydigt trykte brudenergi er udeladt | [Alonso m.fl.](https://doi.org/10.3989/mc.2013.01412) |

En materialefamilie kan have mange prøver. Vælg eksempelvis den stampede jord med 120 mm lag efter én måneds tørring. I trykforsøgene var middelstyrken 0,50 MPa med standardafvigelsen 0,07 MPa.

```sh
ft-materials facts mechanics-minerals:material:shrestha-2020-120-1 --field compressive_strength
```
