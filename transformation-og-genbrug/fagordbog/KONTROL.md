# Hvad er kontrolleret?

Bladene viser navne, placering og form i udvalgte byggeprincipper. SolidCraft 0.45.0 har bygget de redigerbare modeller ud fra de medfølgende opskrifter. De nye tegninger er tegnet af Fremtidens Tegnestue. Kildelinket ved hvert ord fører til fagteksten, en original detaljetegning eller producentens beskrevne variant. Et produktsnit er brugt til at forstå delens placering. Modellernes mål er illustrative.

## Gennemgang pr. blad

| Blad | Opslag | Lukkede CAD-legemer | Fagligt sammenhold med originalerne |
| --- | ---: | ---: | --- |
| [Når tag og ydermur mødes](README.md) | 6 | 11 | Skalkens kile og tremplens højde i hver sit snit. |
| [Vinduet](vindue/README.md) | 10 | 18 | Posten hører til karmen, sprossen til rammen. Kit og glasliste vises i hver sin fals. |
| [Døren](doer/README.md) | 8 | 15 | Gerigt og indfatning er samme del. Slutblikket sidder modsat det hængslede beslag. |
| [Resten af taget](tag/README.md) | 11 | 22 | På tagplanen leder flader vand mod kelen og bort fra graten. Skotrenden ligger langs kelen. |
| [Facade og murværk](murvaerk/README.md) | 9 | 34 | Stikkets fuger fordeler sig over åbningen. Fals og overligger vises i forskellige snit. |
| [Træ, bindingsværk og samlinger](bindingsvaerk/README.md) | 9 | 14 | Tappen rager ud, og taphullet er en åbning. Løsholt og tavl ligger mellem stolperne. |
| [Dæk, gulv og loft](daek/README.md) | 7 | 14 | Bjælkeenden har et leje i muren. Indskud, forskalling og puds ligger i forskellig højde. |
| [Trappe og adgang](trappe/README.md) | 8 | 20 | Grund måles vandret mellem forkant og forkant. Vange og håndliste forløber i forskellige højder. |
| [Sokkel, terræn og kælder](fundament/README.md) | 7 | 20 | Terrændæk, krybekælder og syldsten vises som forskellige varianter. |
| [Beton, stål og montage](beton/README.md) | 8 | 13 | Kanalerne ses i tværsnit, understøtningen i længdesnit. Dæklaget måles til stålets yderside. |
| [Klimaskærmens lag](klimaskaerm/README.md) | 6 | 11 | Dampbremse og dampspærre vises som alternativer; vindspærren sidder udvendigt på isoleringen. |
| [Vand, varme og ventilation](installationer/README.md) | 8 | 17 | Vandlåsen har et vandspejl. Stigstrengen hører til varmeanlægget og spjældet til ventilationen. |
| [Uderum og afvanding](uderum/README.md) | 6 | 15 | Nedløbet er vist oven for brønden. Den åbne rendes profil vises på tværs. |
| [Spor, reparation og genbrug](reparation/README.md) | 7 | 32 | Fugen vises før, under og efter indgrebet. Lask og lus vises i separate træstykker. |

## Efterkontrol af de 110 pegepunkter

[Pegepunktsregisteret](pegepunkter.tsv) knytter hvert nummer til tegning, fagord, endepunkt og originalkilde. Koordinaterne hører til den enkelte SVG-tegning. Ved et materiale rammer prikken delen eller dens kant. Ved et område ender henvisningslinjen på den stiplede afgrænsning, og ved et mål ender den på klammen.

| Blad | Hvad blev efterset eller rettet? |
| --- | --- |
| Tagfod | Tremplens klamme følger højden fra gulv til rem. Linjen til tagfoden slutter nu på den stiplede bue. |
| Vindue | Punkt 9 rammer det indvendige hjørne i træets kitfals. Bundsnittet viser nu også understøtningen ved forsatsrammen. |
| Dør | Slutblikket og karmen har en åbning til fallen. Punkt 7 rammer metallet over åbningen. |
| Tag | Rygningsstenene dækker kun en del af kiplinjen i tagplanen. Lægterne ligger an mod afstandslisten. Kvistens tag, front og flunk kan følges hver for sig. |
| Murværk | Klammen ud for øverste række angiver ét skifte. Den stiplede markering for forbandt omfatter forskudte studsfuger. |
| Bindingsværk | Tap, taphul og dyvel er gennemgået i den adskilte samling. Punkt 7 ender på markeringen omkring åbningen i træet. |
| Dæk | Punkt 1 rammer bjælkens endeflade i murlommen. I tværsnittet hviler indskudsbrædderne nu på lister ved bjælkesiderne. |
| Trappe | Punkt 2 rammer stødtrinnets bræt. Klammen for grund spænder vandret mellem to trinforkanter. |
| Fundament | Fodremmen har en anlægsflade på syldstenen. Punkt 6 rammer lyskassens væg. |
| Beton | Dæklagsklammen går fra stålets overflade til betonens yderside. Opslagene om stål og dæklag henviser til fagafsnittet hos CRH. Søjle og konsol henviser til producentens søjlevariant. |
| Klimaskærm | De tre lag kan følges fra vindspærren gennem isoleringen til dampspærren. Facadesnittets henvisning åbner nu ved tegningen på PDF-side 89. |
| Installationer | Punkt 2 rammer grenrørets væg. Afløbsskålen er åben ned til vandlåsen, og punkt 4 rammer skålens side. |
| Uderum | Kantstenen ligger ved belægningens høje side. Fra stenene kan man følge faldet til rendens kant. |
| Reparation | Den udkradsede fuge markeres som et område. Ved omfugning, udlusning og påforing rammer prikkerne det tilførte materiale. |

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
