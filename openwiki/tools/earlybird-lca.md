---
type: reference
title: "EarlyBird LCA"
description: "Overslags-LCA fra geometri og materialer i tidlige designfaser."
tags: ["vandkunsten", "earlybird-lca", "tool"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T23:08:02.924Z
sources:
  - id: openwiki-source-ad4b3c306dd228fe019c57fc
    resource: repo://extracted/opensource.vandkunsten.com/03_earlybird-lca/index.txt
generated: { by: "codex", at: "2026-11-17T23:08:02.924Z" }
---

# EarlyBird LCA

Overslags-LCA fra geometri og materialer i tidlige designfaser.

Originalside: [EarlyBird LCA](https://opensource.vandkunsten.com/03_earlybird-lca/). Platform: **Excel**.

## Originalfiler hos udgiveren

| Fil | Størrelse |
| --- | ---: |
| [VK_EarlyBird_v4.xlsx](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx) | 64,283 byte |
| [VK_earlybirdLCA_500x500.jpg](https://opensource.vandkunsten.com/03_earlybird-lca/VK_earlybirdLCA_500x500.jpg) | 157,876 byte |

## Metode og begrænsninger

Vandkunsten beskriver værktøjet som en overslagsberegning fra geometri og materialer i de tidlige designfaser. Datagrundlaget er aggregerede bygningsdele med ÖKOBAUDAT 2015 og betragtningsperioder på 1, 50 og 60 år.

Siden beskriver fire sammenligninger med LCAbyg fra 2016 og afvigelser på op til 20 %. Tallet er en observation fra disse sammenligninger, ikke et generelt statistisk usikkerhedsinterval.

Workbooken indeholder `InputData`, `Results`, den skjulte `Calc`, `Database`, `license` og den skjulte `menu`. Arkivudtrækket bevarer de originale formler og celleplaceringer uden genberegning.

## Muligt genbrug

Dette er et oplagt udgangspunkt for en motor til scenariesammenligning. En senere port skal holde geometriske antagelser, mængder, materialedata, levetider og beregningsperiode adskilt. Gem historiske data som reference, når nyere data tilføjes.

## Kontrolstatus og rettigheder

ÖKOBAUDAT 2015; siden beskriver afvigelser på op til 20 % i fire sammenligninger.

MIT angivet på site og licensark. Ingen upstream-programmer eller makroer er afviklet.

[Projektregister](../../catalog/projects.json) · [Filregister](../../catalog/files.json) · [Workbook-register](../../catalog/workbooks.json) · [ZIP-manifest](../../catalog/archives.json) · [PDF-register](../../catalog/pdfs.json)

## Inspicerede Excel-faner

- [InputData](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx): visible, 67 formelceller.
- [Results](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx): visible, 299 formelceller.
- [Calc](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx): hidden, 25 formelceller.
- [Database](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx): visible, 0 formelceller.
- [license](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx): visible, 0 formelceller.
- [menu](https://opensource.vandkunsten.com/03_earlybird-lca/VK_EarlyBird_v4.xlsx): hidden, 0 formelceller.

I den offentlige Git-pakke peger links til originalfiler og regnearksfaner på udgiverens filer. Det fulde lokale arkiv og JSON-celleudtræk kan genskabes; se [arkivguiden](../../docs/ARKIV.md).
