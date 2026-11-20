# Sådan bruger du SolidCraft, BIMCraft og FieldCraft sammen

Forestil dig, at du vil genbruge en facadeplade og tegne et nyt beslag til den. I **BIMCraft** finder du pladen på bygningen. I **SolidCraft** tegner du beslaget. I **FieldCraft** kan du undersøge, hvor meget beslaget bøjer, når det bærer pladen. **Materialeværktøjet** hjælper dig med at finde de tal, der passer til hvert spørgsmål, og viser, hvor de kommer fra.

| Hvad vil du vide? | Værktøj | Sådan kan du bruge det |
| --- | --- | --- |
| Hvor sidder pladen, og hvad skal bevares? | **BIMCraft** | Find etagen, væggen og bygningsdelen. Registrér eksisterende og nye dele, lav tegninger og mængdelister, eller udveksl bygningsmodellen som IFC. [Hent BIMCraft og læs vejledningen](https://github.com/IPedrax/BIMCraft) |
| Hvordan skal beslaget se ud? | **SolidCraft** | Tegn formen med mål. Flyt et skruehul eller ændr ståltykkelsen, og lad modellen opdatere geometrien. [Hent SolidCraft](https://solidcraft.io/download/) · [Vejledning](https://docs.solidcraft.io/) |
| Hvad sker der, når beslaget belastes? | **FieldCraft** | Angiv stålets egenskaber, hvor beslaget holdes fast, og hvor lasten virker. Programmet deler geometrien i små beregningselementer og beregner blandt andet nedbøjning, spændinger og kræfter ved understøtningerne. [Hent FieldCraft](https://github.com/tangency-labs/fieldcraft/releases) · [Vejledning til statiske beregninger](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/linear-static.md) |
| Hvilke materialetal gælder her? | **Vores Rust-værktøj, `ft-materials`** | Brug den valgte plades densitet til vægt og dens miljødeklaration til produktionsklima. Til en beregning af beslaget kan du slå den valgte stålkvalitets stivhed op. Værktøjet viser også enhed, kilde og forsøgsbetingelser. [Mekaniske materialedata](sources/mekanik.md) · [Installation og første opslag](RUST.md) |

## Et forsøg, du kan gentage

Vi tegnede en fiberbetonplade på 1 × 0,5 meter i SolidCraft og overførte den til BIMCraft. En GLB-fil bar formen fra det ene program til det andet. Vi knyttede begge modeldele til den samme produktdeklaration for Lindners LinCrete. Den angiver en densitet på 2.100 kg/m³. På den måde kunne materialeværktøjet beregne vægt og klima ud fra hver models eget volumen. [Modeller, kommandoer og kontrolresultater](../examples/unified-workflow/README.md) · [Produktdeklaration](https://oekobaudat.de/OEKOBAU.DAT/resource/processes/c54c16f6-4295-4749-bff0-ba7ed4bc9117?format=json&view=extended&version=00.01.000)

| Pladetykkelse | Vægt fra SolidCraft-modellen | Vægt fra BIMCraft-modellen | Klimaaftryk for produktionen (A1–A3) |
| --- | ---: | ---: | ---: |
| 20 mm | 21,0 kg | 21,0 kg | 17,79 kg CO₂e |
| 24 mm | 25,2 kg | 25,2 kg | 21,35 kg CO₂e |

Du kan selv kontrollere den første vægt ved at gange 1 m × 0,5 m × 0,020 m × 2.100 kg/m³. De ekstra fire millimeter gør pladen 4,2 kg tungere.

## Fra pladens vægt til beslagets nedbøjning

To ens beslag kan bøje forskelligt under samme vægt. Det har betydning, om pladen hviler tæt på væggen eller længere ude på beslaget. Før en beregning i FieldCraft skal du derfor kende lastens størrelse og placering, stålets egenskaber og den måde, beslaget er fastgjort på. Ved genbrug kan korrosion, gamle huller eller usikkerhed om stålkvaliteten kræve opmåling eller prøvning.

I hyldeeksemplet har vi gennemført hele forløbet. SolidCraft og BIMCraft gav de samme mængder for en plade og to stålskinner. Rust-værktøjet slog de valgte materialers egenskaber op og sendte stålets stivhed til FieldCraft. Vi overførte skinnen som en flademærket 3MF-fil, så beregningen kunne skelne vægfladen fra den frie ende. Ved en samlet frontlast på 100 N fik hver skinne 50 N. FieldCraft gav 0,851 mm nedbøjning pr. skinne på det fine net. En uafhængig bjælkeformel gav 0,857 mm. [Hylden med modeller og beregninger](../examples/hyldekonsol/README.md) · [FieldCrafts materialemodeller](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/materials.md)

## Prøv med din egen AI-agent

> Find facadepladen i bygningsmodellen, og sammenlign to tykkelser på det nye beslag. Vis vægt og produktionsklima for hver løsning med kilde og enhed. Find de oplysninger, der skal til for at beregne nedbøjningen. Fortæl mig, hvad jeg skal måle eller beslutte.

Agenten kan bruge modelprogrammernes kommandolinjer og slå op i de samme materialedata som dig. Bed den gemme modelrevisionen og de valgte kilder sammen med resultatet. Så kan en kollega gentage beregningen og se, hvilke antagelser der skal vurderes, før beslaget bruges i byggeriet. [Guide til fælles materialevalg på tværs af modeller](../examples/unified-workflow/README.md)
