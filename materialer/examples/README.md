# Vælg et eksempel

[SolidCraft → BIMCraft → materialeværktøj](integrated-workflow/README.md) viser den samme tredelte model, en tykkelsesændring, vægt og produktionsklima samt kontrol af geometri på returen. Der følger faktiske `.sc`- og `.bimc`-modeller, GLB-filer, materialekort og beregningsresultater med.

Du kan læse forklaring og gemte resultater i browseren. Installation er først nødvendig, når du vil køre et opslag, en beregning eller en model selv.

| Det vil du prøve | Eksempel | Kræver, hvis du selv vil køre det |
| --- | --- | --- |
| Se, hvordan en ændret tykkelse påvirker vægt og produktionsklima | [Betonpladen med to stålskinner](integrated-workflow/README.md) | Følg eksemplets særskilte model- og beregningstrin. |
| Finde dit første materialetal | [Opslag uden database](../docs/KOM-GODT-I-GANG.md#2-slå-materialer-op-uden-database) | Python 3.11+ og PyArrow. |
| Beregne en kendt mængde uden CAD | [Referenceberegningen med 500 kg](../README.md#din-første-beregning) | Aktuel Rust-CLI og dens dataudgave. |
| Følge samme materialevalg gennem to modelprogrammer | [SolidCraft og BIMCraft](unified-workflow/README.md) | Rust og de angivne versioner af modelprogrammernes CLI'er. |
| Undersøge en hyldes nedbøjning | [Hylde med FieldCraft-kontrol](hyldekonsol/README.md) | Rust, modelprogrammer og FieldCraft som beskrevet i eksemplet. |
| Undersøge reparation og udtagning af dele | [De to vindueseksempler](../docs/DISASSEMBLY.md) | Rust bygget fra samme aktuelle kode som dataene. Resultaterne er delvise scenarier. |

Forløbene har forskelligt omfang. En korrekt prøveberegning eller en geometrisk model er ikke en godkendelse af en konstruktion, et produktvalg eller en hel bygnings LCA.

## Kontrolmodeller og grundlagsfiler

- [SolidCraft-kontrolmodeller](models/solidcraft/README.md): materialefamilier og en ekstra prøve på fugtbevægelse.
- [BIMCraft-kontrolmodeller](models/bimcraft/README.md): kendte mængder og kontroller af manglende/blandede materialer.
- [Bindingsfiler](bindings/): eksplicitte forbindelser mellem modelversion, element og kildeobservation.
- [Requests](requests/): små beregninger med en kendt mængde, som ikke kræver et modelprogram.
- [Gemte resultater](reports/): JSON med mængder, beregninger og kilder.

Følg [startvejledningen](../docs/KOM-GODT-I-GANG.md), og vælg først database-/Rust-installationen, når det valgte forløb kræver den. Parquet-opslaget kræver ingen database. Eksemplernes egne anvisninger beskriver eventuel hentning af originalkilder og modelprogrammer.

Gemte rapporter dokumenterer deres angivne input og kørsel. Nye modeller skal have egne aktuelle materialebindinger og forudsætninger. [Kontrolomfang og versionskrav](../docs/VALIDATION.md).
