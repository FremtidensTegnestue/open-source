---
type: reference
title: "FieldCraft og samspillet med SolidCraft og BIMCraft"
description: "Find værktøjet til geometri, bygningsmodel eller statik, og se hvordan materialedata bruges i et facadeeksempel."
tags: ["programs", "cad", "bim", "simulation"]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-20T21:01:37.522Z
sources:
  - id: openwiki-source-d381c97b524d3c90f09bd9b5
    resource: repo://docs/PROGRAMMER.md
  - id: openwiki-source-80736ab9af9fdefbbb92749c
    resource: repo://examples/unified-workflow/README.md
generated: { by: "codex", at: "2026-11-20T21:01:37.522Z" }
---

# Hvilket program skal jeg bruge til en facadeplade?

Find pladen på bygningen i [BIMCraft](bimcraft.md). Tegn dens beslag med præcise mål i [SolidCraft](solidcraft.md). Hvis du vil vide, hvor meget beslaget bøjer under last, kan du bruge **FieldCraft**. Her skal du angive, hvor beslaget er fastholdt, hvor lasten virker, og hvilke egenskaber stålet har. [FieldCrafts vejledning til statik](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/linear-static.md)

Materialeværktøjet giver din agent adgang til både tal og kilder. I vores forsøg gav den samme fiberbetonplade 21,0 kg ved 20 mm tykkelse og 25,2 kg ved 24 mm, uanset om mængden kom fra SolidCraft eller BIMCraft. GLB overførte geometrien, og pladen i hver model blev knyttet til den samme produktdeklaration. En samlet statisk beregning med geometri, vores materialetal og FieldCraft mangler fortsat at blive afprøvet. [Det dokumenterede forsøg](../../examples/unified-workflow/README.md)

[Læs hele programguiden med en opgave til din egen agent](../../docs/PROGRAMMER.md) · [Find materialetal til den statiske analyse](../../docs/sources/mekanik.md)
