---
type: reference
title: "Arkiv, katalog og proveniens"
description: "Forstå arkivets omfang, filregistre, kontrolsummer, upstream-snapshot og manglende kilder."
tags: ["archive", "provenance", "catalog"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-17T18:53:24.356Z
sources:
  - id: openwiki-source-16ad9c57da182f87c66c86c2
    resource: repo://catalog/coverage.json
  - id: openwiki-source-77c8888fdb66f4f7e0daeca9
    resource: repo://catalog/downloads.json
  - id: openwiki-source-4045c76b58c93abdab35a36a
    resource: repo://catalog/upstream.json
generated: { by: "codex", at: "2026-11-17T18:53:24.356Z" }
---

# Arkiv, katalog og proveniens

## Arkivets lag

Originale HTTP-downloads ligger under `archive/<værtsnavn>/<original sti>`. HTML er bevaret som hentet, uden omskrivning af links. Derfor er originalspejlet ikke en færdig offline-hjemmeside; brug wikiens lokale filhenvisninger.

`upstream/Daylight_VK-01/` er et uændret snapshot af GitHub-arbejdsfilerne. `catalog/upstream.json` registrerer repository, commit og Git-bundle. Snapshot og historik kan dermed identificeres særskilt fra hjemmesidens downloads.

`unpacked/` indeholder afledte kopier fra ZIP-filer. `catalog/archives.json` registrerer hver pakke, indhold, udpakket sti og CRC-kontrol. Originale arkiver bevares, også når et indlejret arkiv pakkes ud.

## Maskinlæsbare registre

| Register | Anvendelse |
| --- | --- |
| [projects.json](../../catalog/projects.json) | Otte projekter med formål, platform, lokale downloads og begrænsninger |
| [downloads.json](../../catalog/downloads.json) | URL, slutadresse, tidspunkt, HTTP-status, indholdstype, størrelse og SHA-256 |
| [supplemental-downloads.json](../../catalog/supplemental-downloads.json) | Alternative dokumentadresser og deres hentestatus |
| [files.json](../../catalog/files.json) | Originale og afledte filer med SHA-256 og størrelse |
| [archives.json](../../catalog/archives.json) | ZIP-indhold og CRC-kontrol |
| [workbooks.json](../../catalog/workbooks.json) | Faner, synlighed, formelantal, VBA-tilstedeværelse og udtræksstier |
| [pdfs.json](../../catalog/pdfs.json) | Sidetal, tekstudtræk og fejl |
| [dynamo.json](../../catalog/dynamo.json) | Dynamo-filformat og tilgængelige kodeudtræk |
| [coverage.json](../../catalog/coverage.json) | Afgrænsning, reddede links og mangler |
| [summary.json](../../catalog/summary.json) | Samlede antal, størrelser og udtræksfejl |

Filregisteret dækker arkiv, upstream, udpakkede filer og søgeudtræk. Det omfatter ikke egne wiki- og katalogfiler rekursivt, og byte-totalen omfatter flere repræsentationer af samme materiale.

## Dækning og fejl

Alle 38 fundne ressourcer på opensource-domænet blev hentet. Det omfatter ni HTML-sider, downloads, billeder, typografi og øvrige assets. Eksterne sites er ikke fuldt spejlet.

SBi-linket returnerede HTML med en PDF-lignende filadresse. Responsen bevares som historisk evidens, men PDF-registeret markerer den som ugyldig PDF. En faktisk rapportkopi er hentet fra AAU via `ws/portalfiles/portal/329648206/SBi_2020_04.pdf`.

Dagslystutorialens GitHub-blob er en HTML-side. Den faktiske PDF findes i repository-snapshottet og som separat historisk raw-download.

Konferenceartiklen om LCA/BIM kunne ikke hentes: konferencens server returnerede HTTP 525, og forsøg på DTU-adresser returnerede 403/404. Den er registreret som manglende. Øvrige eksterne referenceadresser findes i `external-links.json`.
