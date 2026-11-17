# Eksempler — begynd med det samlede forløb

[SolidCraft → BIMCraft → materialeværktøj](integrated-workflow/README.md) viser den samme tredelte model, en tykkelsesændring, vægt og produktionsklima samt kontrol af geometri på returen. Der følger faktiske `.sc`- og `.bimc`-modeller, GLB-filer, materialekort og beregningsresultater med.

Andre indgange:

- [SolidCraft-kontrolmodeller](models/solidcraft/README.md): materialefamilier og en ekstra prøve på fugtbevægelse.
- [BIMCraft-kontrolmodeller](models/bimcraft/README.md): kendte mængder og kontroller af manglende/blandede materialer.
- [Bindingsfiler](bindings/): eksplicitte forbindelser mellem modelversion, element og kildeobservation.
- [Requests](requests/): små beregninger med en kendt mængde, som ikke kræver et modelprogram.
- [Gemte resultater](reports/): JSON med mængder, beregninger og kilder.

Før nye beregninger skal [hele databasen gendannes](../data/README.md). Originaldokumenter til de uafhængige kontrolberegninger hentes med `python scripts/fetch_sources.py --demo`. Gamle rapporter er bevis for en bestemt kørsel; nye modeller skal have deres egne aktuelle bindingsfiler.
