# Dansk grundlag for levetid og driftsøkonomi

## Levetiden for en bygningsdel

BUILDs tabel fra december 2021 indeholder middellevetider på fire detaljeringsniveauer. Den lokale import læser de fire originale regneark og opretter en særskilt reference for hver udfyldt kombination af bygningsdel og materialekolonne. Man kan eksempelvis søge efter etagedæk og vælge den relevante kombination af konstruktion og materiale. Svaret fører tilbage til den konkrete celle. Generelle værdier, materialspecifikke værdier og markeringen »Ikke relevant« kan ses hver for sig. En tom celle i krydstabellen opretter ingen materialepost. [Haugbølle, Mahdi, Morelli og Wahedi, BUILD Rapport 2021:32, 2. udgave](https://vbn.aau.dk/da/publications/build-levetidstabel-version-2021/)

```sh
ft-materials collect-lifetimes
ft-materials build --supplement data/staging/build-levetid
ft-materials search etagedæk --dataset build-levetid
ft-materials facts build-levetid:2021:l4:I6 --field service_life_value
```

Den sidste kommando læser cellen I6 i arket »Bygningsdele SfB«. Den angiver 120 år for pælefundamenter og brøndfundamenter i kolonnen »Beton, terrazzo og cementmørtel«. Tallet er et dansk referencegennemsnit for denne kombination. Ved projektering kan man også have en produktdeklaration med en anden levetid under andre betingelser. Vælg og begrund kilden i projektet.

Udgiveren angiver rettigheder til lokal brug ved privat studium eller forskning. CLI’et henter det originale regneark fra Aalborg Universitet og kontrollerer SHA-256. Den offentlige kode kan genskabe tillægget lokalt. Oprindelse, rettigheder, fane, række og kolonne følger de enkelte poster. Importen er låst til december 2021. [Originalt regneark](https://vbn.aau.dk/ws/portalfiles/portal/568162944/BUILD_levetidstabel_december_2021.xlsx)

## Levetid og omkostninger for varmeanlæg

Energistyrelsens teknologikatalog fra april 2026 beskriver 45 teknologiscenarier for opvarmning af boliger. Den offentlige pakke indeholder alle 7.449 numeriske estimater i teknologifanernes ni årskolonner og registrerer de 2.766 tomme estimatceller særskilt. Årgangene er 2025, 2030, 2035, 2040 og 2050. I 2025 og 2050 findes der desuden kolonner med lave og høje skøn. Driftsomkostninger, installation, effekt, energiydelse og levetid kan slås op på den samme scenariepost. Priserne er angivet i faste 2025-euro eksklusive moms og øvrige skatter. Enkelte rækker mangler enhed i originalen. [Original XLSX med CC BY 4.0 i fanen Index](https://ens.dk/media/8518/download) · [Energistyrelsens metode og afgrænsning](https://ens.dk/media/8516/download)

```sh
ft-materials collect-heating
ft-materials facts ens-varme:scenario:c48c49772f45da4a --field service_life_value
ft-materials facts ens-varme:scenario:c48c49772f45da4a --field work_cost --limit 5
```

Luft-til-vand-varmepumpen i et eksisterende enfamiliehus har for 2025 et centralt teknisk-økonomisk levetidsskøn på 20 år. Det lave skøn er 14 år og det høje 25 år. Man kan kontrollere dem i C11, H11 og I11 på fanen »207 HP air-water,ex single«. Et bestemt fabrikat kan have andre forhold. Under `conditions` findes scenariets navn, regnearkets parameternavn, fremskrivningsår, typen af skøn samt noterne og referencerne fra rækken. Den oprindelige enhed bevares, herunder forskellen mellem euro og tusinde euro. [Det originale datasæt medfører attribution til Energistyrelsen](../../data/supplements/ens-varme/sources.jsonl)
