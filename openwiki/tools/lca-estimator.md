---
type: reference
title: "LCA estimator"
description: "Estimerer tidlig LCA ved match mod bygningscases fra SBi 2020:04."
tags: ["vandkunsten", "lca-estimator", "tool"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-0101a96653d9b72a703ba8d5
    resource: repo://extracted/opensource.vandkunsten.com/01_lca-estimator/index.txt
  - id: openwiki-source-c09a783c76487fe6a4e02cce
    resource: repo://extracted/pdf/archive/opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimator-metode.txt
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# LCA estimator

Estimerer tidlig LCA ved match mod bygningscases fra SBi 2020:04.

Originalside: [LCA estimator](https://opensource.vandkunsten.com/01_lca-estimator/). Platform: **Excel 365 / VBA**.

## Originalfiler hos udgiveren

| Fil | Størrelse |
| --- | ---: |
| [VK_LCAestimator-metode.pdf](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimator-metode.pdf) | 1,692,637 byte |
| [VK_LCAestimator500x500.jpg](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimator500x500.jpg) | 143,080 byte |
| [VK_LCAestimatorV2.xlsm](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm) | 124,558 byte |

## Metode og datagrundlag

Værktøjet matcher overordnet materialitet og areal med cases fra SBi 2020:04. Den medfølgende metodepræsentation beskriver en vægtet matchscore for op til ni bygningsdele og udvælgelse af tre cases med højest score. Det er en analogibaseret estimering, hvis anvendelighed afhænger af repræsentative cases.

Den originale workbook har VBA og skjulte faner til databaser, beregning, menuer og vægtning af bygningsdele. JSON-udtrækkene gør også disse faner tilgængelige. Koden til VBA er bevaret i den originale `.xlsm`; den er ikke dekompileret eller afviklet.

SBi-rapportens oprindelige link returnerede HTML. Den faktiske PDF findes i `archive/vbn.aau.dk/ws/portalfiles/portal/329648206/SBi_2020_04.pdf`.

## Muligt genbrug

Adskil caseregister, vægtningsregler og matchalgoritme. Dokumentér referencecases og verificér, at en fremtidig implementation vælger samme matches, før datasættet opdateres. En agent bør modtage matchbegrundelse og dataversion sammen med resultatet.

## Kontrolstatus og rettigheder

Datasæt fra 2020; repræsentative cases er nødvendige.

MIT angivet på site og licensark. Ingen upstream-programmer eller makroer er afviklet.

[Projektregister](../../catalog/projects.json) · [Filregister](../../catalog/files.json) · [Workbook-register](../../catalog/workbooks.json) · [ZIP-manifest](../../catalog/archives.json) · [PDF-register](../../catalog/pdfs.json)

## Inspicerede Excel-faner

- [forside](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): visible, 18 formelceller.
- [license](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): visible, 0 formelceller.
- [db_LCA](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 1080 formelceller.
- [db_LCA50](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 0 formelceller.
- [db_LCA80](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 0 formelceller.
- [diagram](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 173 formelceller.
- [menuer](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 0 formelceller.
- [beregning](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 154 formelceller.
- [andel bygningsdele](https://opensource.vandkunsten.com/01_lca-estimator/VK_LCAestimatorV2.xlsm): hidden, 20 formelceller.

I den offentlige Git-pakke peger links til originalfiler og regnearksfaner på udgiverens filer. Det fulde lokale arkiv og JSON-celleudtræk kan genskabes; se [arkivguiden](../../docs/ARKIV.md).
