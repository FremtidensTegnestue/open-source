---
type: reference
title: "Søgning, udtræk og genkatalogisering"
description: "Brug og gendan de søgbare afledninger uden at udføre historiske programmer eller makroer."
tags: ["workflow", "extraction", "operations"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T18:53:24.356Z
sources:
  - id: openwiki-source-91d62cdd74ebb1dee4563c68
    resource: repo://catalog/summary.json
  - id: openwiki-source-07eb7a94b6fabeea990aaf56
    resource: repo://catalogue.py
  - id: openwiki-source-074fff1ea019bf34b1469f14
    resource: repo://harvest.py
generated: { by: "codex", at: "2026-11-17T18:53:24.356Z" }
---

# Søgning, udtræk og genkatalogisering

## Søg før åbning af originalprogrammer

Find projektet i `catalog/projects.json`. Brug `rg` i `extracted/` til tekstsøgning, og følg derefter originalstien i kataloget. PDF-udtræk har sidemarkeringer eller sideopdeling; tabeller og tegninger kan have tabt layout. Det er ikke OCR.

Excel-udtræk ligger i `extracted/workbooks/<original sti>/<fanenummer>-<fanenavn>.json` og tilsvarende CSV. JSON har celleadresser, celletyper, værdier og formler. CSV er til inspektion; indhold med indledende lighedstegn er originale formler og skal ikke forveksles med allerede beregnede resultater.

Skjulte faner udtrækkes sammen med synlige faner. `has_vba` registrerer tilstedeværelse af VBA i ZIP-containeren; scriptet udtrækker eller kører ikke selve VBA-koden. Excel-filerne bliver ikke gemt igen med openpyxl, så originalernes funktioner og makroer bevares.

Dynamo-udtræk er fundne kodefragmenter i JSON/XML-definitioner, ikke en fuld beskrivelse af alle forbindelser og plugin-afhængigheder. Binære Grasshopper-definitioner er arkiveret uden rekonstruktion.

## Genhentning

Kør fra roden:

```sh
python3 harvest.py
```

Scriptet gennemløber lokale sitehenvisninger og direkte eksterne dokumentlinks. Eksisterende vellykkede downloads genbruges fra manifestet. Det er en genoptagelsesmekanisme, ikke en garanti for at opdage ændringer på en allerede hentet URL. Alternative rapportlinks og GitHub-snapshot er dokumenteret separat.

## Genkatalogisering

```sh
python3 catalogue.py
```

Kommandoen kræver `openpyxl` og `pypdf`. Den pakker ZIP-filer og indlejrede ZIP-filer ud, kontrollerer CRC, udtrækker Excel-faner, læser PDF-tekst og katalogiserer Dynamo. Stier med absolutte filnavne eller `..` afvises ved udpakning, og ZIP-symlinks springes over.

Det første katalog er suppleret med projekternes beskrivelser og en særskilt dækningsrapport. `catalogue.py` gendanner de tekniske kataloger; det opdaterer ikke selv denne faglige wiki eller alle manuelt afklarede kildeforhold. Afstem dækningsrapport og wiki efter en ny høst.

## Kontrolniveau

Der er ingen rapporteret ZIP-CRC-fejl eller workbook-udtræksfejl i det første katalog. Den gamle SBi-respons er registreret som ikke-PDF. Kontrolsummer og filintegritet dokumenterer filerne; de validerer ikke beregningsmetoder eller nutidig programkompatibilitet.
