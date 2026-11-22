<!-- OPENWIKI:START -->

## OpenWiki

This repository has a generated `openwiki/` evidence index. It is optional just-in-time context, not required startup reading.

- Do not enumerate, preload, or search wikis at task start. Use retrieval when the user asks for it, when unfamiliar architecture or dependency behavior materially affects the task, or when source inspection leaves an important uncertainty. Stop once the question is grounded.
- When those conditions apply and OpenWiki retrieval tools are available, use `openwiki_search` for just-in-time context and `openwiki_read` for the relevant complete sections. If search returns `workspace_required`, ask which listed workspace to use and retry with its ID.
- Use `openwiki_list_workspaces` or `openwiki_list_wikis` when workspace membership itself needs to be discovered.
- If the retrieval tools are unavailable, read `openwiki/quickstart.md` and follow its links to the relevant pages.
- Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements.
- Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output.

Use the repository's documented maintenance process to refresh generated pages after source changes. Check its configuration and completed runs before relying on automatic updates. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->

## Live modelkobling

Ved flere lokale CAD-instanser er discoveryfilens seneste port ikke automatisk brugerens synlige vindue. Kontrollér appinstans, dokument/projektidentitet og faktisk UI hver for sig, og fasthold den valgte forbindelse under arbejdet. Bevar eksisterende dokumenter og ugemte tilstande; en fungerende baggrundssession er ikke bevis for brugerens oplevelse. Se facadeeksemplets dokumenterede afgrænsning og acceptprøver før et nyt live-/panel-løfte.

## Enkel og ærlig regnskabsvisning

Vis først konsekvens og få konkrete næste handlinger; fold kilde-/grundlagsdetaljer ud efter behov. Nye parametre skal have en konkret beslutning, beregning eller afklaring som modtager. Registreret dokumentation er ikke teknisk eftervist; en levetid og et hændelsesantal er ikke en beregnet livscyklus. Skift af valgt del/fag i en formular er visningskontekst og må ikke skabe nye input eller gøre ukendte felter til nul. Se den faktiske facadefunktion og docs/DESIGN-TOOL-REVIEW-2026-11-21.md før nye produktløfter.

## Udfør eget arbejde og vis resten

Brugerens seneste regel: Vi udfører selv alt arbejde, som opgavens faktiske grundlag, metode, kompetencer og regler tillader. Manglende oplysninger eller en uprøvet metode udløser en konkret undersøgelse eller afklaring, ikke automatisk outsourcing. Påkrævede personroller, autoriseret udførelse og formelle erklæringer må ikke erstattes af AI eller softwaretests.

Efter hvert væsentligt trin opdateres en enkel arbejdsoversigt: præcist omfang, eget/særskilt/uafklaret arbejde, ansvarlig rolle, næste handling, manglende grundlag og nødvendig faglig kontrol eller formel godkendelse. Uafklarede krav forbliver uafklarede; opfind ikke et certifikationskrav eller en rådgiveraftale. Afklar kritisk grundlag og kontrol tidligt frem for at søge en underskrift til sidst. Luk kun en post med konkret bilag, faktisk kontrolomfang, ansvar og dato. Ændret grundlag kræver genvurdering af berørte poster. Ingen samlet grøn status eller færdigprocent udledes af delkontroller. Se [den afgrænsede arbejdsoversigt](examples/work-overview/README.md); den registrerer dokumentation og kontrollerer filbindinger, men udsteder ingen faglig/formel godkendelse.
