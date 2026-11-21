# Hvad er kontrolleret?

Bladene viser navne, placering og form i udvalgte byggeprincipper. SolidCraft 0.45.0 har bygget de redigerbare modeller ud fra de medfølgende opskrifter. De nye tegninger er tegnet af Fremtidens Tegnestue. Kildelinket ved hvert ord fører til fagteksten, en original detaljetegning eller producentens beskrevne variant. Et produktsnit er brugt til at forstå delens placering. Modellernes mål er illustrative.

## Gennemgang pr. blad

| Blad | Opslag | Lukkede CAD-legemer | Fagligt sammenhold med originalerne |
| --- | ---: | ---: | --- |
| [Når tag og ydermur mødes](README.md) | 6 | 11 | Skalkens kile og tremplens højde i hver sit snit. |
| [Vinduet](vindue/README.md) | 10 | 18 | Posten hører til karmen, sprossen til rammen. Kit og glasliste vises i hver sin fals. |
| [Døren](doer/README.md) | 8 | 14 | Gerigt og indfatning er samme del. Slutblikket sidder modsat det hængslede beslag. |
| [Resten af taget](tag/README.md) | 11 | 20 | På tagplanen leder flader vand mod kelen og bort fra graten. Skotrenden ligger langs kelen. |
| [Facade og murværk](murvaerk/README.md) | 9 | 34 | Stikkets fuger fordeler sig over åbningen. Fals og overligger vises i forskellige snit. |
| [Træ, bindingsværk og samlinger](bindingsvaerk/README.md) | 9 | 14 | Tappen rager ud, og taphullet er en åbning. Løsholt og tavl ligger mellem stolperne. |
| [Dæk, gulv og loft](daek/README.md) | 7 | 12 | Bjælkeenden har et leje i muren. Indskud, forskalling og puds ligger i forskellig højde. |
| [Trappe og adgang](trappe/README.md) | 8 | 20 | Grund måles vandret mellem forkant og forkant. Vange og håndliste forløber i forskellige højder. |
| [Sokkel, terræn og kælder](fundament/README.md) | 7 | 20 | Terrændæk, krybekælder og syldsten vises som forskellige varianter. |
| [Beton, stål og montage](beton/README.md) | 8 | 13 | Kanalerne ses i tværsnit, understøtningen i længdesnit. Dæklaget måles til stålets yderside. |
| [Klimaskærmens lag](klimaskaerm/README.md) | 6 | 11 | Dampbremse og dampspærre vises som alternativer; vindspærren sidder udvendigt på isoleringen. |
| [Vand, varme og ventilation](installationer/README.md) | 8 | 16 | Vandlåsen har et vandspejl. Stigstrengen hører til varmeanlægget og spjældet til ventilationen. |
| [Uderum og afvanding](uderum/README.md) | 6 | 15 | Nedløbet er vist oven for brønden. Den åbne rendes profil vises på tværs. |
| [Spor, reparation og genbrug](reparation/README.md) | 7 | 32 | Fugen vises før, under og efter indgrebet. Lask og lus vises i separate træstykker. |

## Geometri, kilder og læseprøver

For hvert nyt blad blev de tegnede snitflader udtrukket af SolidCraft-eksporten. Fladerne blev sammenholdt med de lukkede CAD-profiler, og areal gange ekstruderingsdybde blev kontrolleret mod SolidCrafts volumen. Programmets interferenskontrol fandt **0 overlap og 0 ukontrollerede par** på hvert af de 14 blade. En tegning af et hulrum, en afstand eller en arbejdsgang kan pege på flere dele eller på luften mellem dem.

Kontrollen kan gentages fra fagordbogens mappe. Skift modelstien for at kontrollere et andet blad.

```sh
solidcraft-cli eval vindue/model.sc
solidcraft-cli run cad/kollision.json --in vindue/model.sc --results
```

På [opslagslisten](OVERSIGT.md) står to konkrete læseopgaver for hvert blad. Opgaverne er klar til afprøvning. Ekstern gennemgang ved en byggesagkyndig og læseprøver med en fagperson og en førstegangslæser udestår. Ved en gennemgang registreres modelrevision, fagperson, dato, den konkrete pegeopgave og eventuelle rettelser. Bæreevne, tæthed og egnethed i en bestemt bygning kræver projektspecifik dokumentation.

## Udgaver af originalkilderne

Læsested og PDF-side står ved det enkelte opslag. Filregisteret identificerer de hentede udgaver med adresse, dato og SHA-256. Rettighederne til originalerne tilhører deres udgivere. [Filregister](../kilder/hentet.tsv) · [Projektets licens](../../LICENSE)
