# Nedbøjning af én stålskinne i FieldCraft

Skinnen er 300 mm lang, 30 mm bred og 10 mm høj. Den indspændes ved væggen, og den samlede kraft på 50 N fordeles over den frie endeflade. Det svarer til den ene skinne, når hyldens to skinner deler en symmetrisk frontlast på 100 N. FieldCraft-forsøget undersøger denne frontlast. Egenvægt indgår i hovedeksemplets særskilte bjælkeberegning.

## Geometri, materiale og last

FieldCraft læser den [flademærkede 3MF-fil fra SolidCraft](../cad/rail.3mf). På legemet `Rail_A` er flade 2 indspændt ved x = 0, og flade 4 er belastet ved x = 300 mm. Lastens størrelse er angivet som en resulterende kraft over hele endefladen. Hver netforfining får dermed samme samlede last. I dette forsøg kunne FieldCraft 0.8.1 læse SolidCraft 0.44.0's mærkede 3MF. Den native CAD-fil brugte designformat 58, og denne FieldCraft-version læste til og med format 57. [SolidCrafts originale formatspecifikation](https://github.com/tangency-labs/solidcraft/blob/v0.44.0/docs/formats/3mf-face-tags.md) · [FieldCrafts importbeskrivelse](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/formats/tagged-mesh.md)

Den lineære, isotrope materialemodel bruger S235-stålets E-modul på 210 GPa og Poissons tal på 0,30. I den samlede Rust-kørsel hentes begge egenskaber fra den fastholdte udgave af `ft-materials`. FieldCraft kører med mm, N og MPa. Koden omregner E fra Pa til MPa og sætter nedad som negativ z. [Kildeværdier](../materialekilder.md) · [FieldCrafts materialemodeller](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/materials.md)

## Hvad viser forsøget?

| Net med kvadratiske seksfladede elementer | Elementer | Knuder | Endens lodrette forskydning | Lodret reaktion ved væggen | Reaktionsmoment ved væggen |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10 mm elementstørrelse | 90 | 798 | −0,84781 mm | +50,0000 N | −15,0000 Nm |
| 5 mm elementstørrelse | 720 | 4.493 | −0,85078 mm | +50,0000 N | −15,0000 Nm |

Nedbøjningen er det aritmetiske gennemsnit af de lodrette forskydninger for knuderne på endefladen. Forfiningen ændrede nedbøjningen med 0,0030 mm. Den klassiske bjælkeberegning giver −0,85714 mm, en forskel på omkring 0,74 % fra det fine net. Reaktionsmomentet er summeret af FieldCraft om vægfladens centrum ved (0, 15, 5) mm. I skinnens midtersnit ved (150, 15, 10) mm gav begge net en normalspænding i skinnens længderetning på +15,0 MPa. Målepunktet ligger på oversiden, hvor skinnen er udsat for træk.

Beregningen forudsætter en ideel fast indspænding, små forskydninger og elastisk stål. Bæreevnen for skruer og væg, den faktiske montages stivhed og hyldens brudlast kræver særskilt dokumentation. [FieldCrafts vejledning til lineær statik](https://github.com/tangency-labs/fieldcraft/blob/v0.8.1/docs/manual/structural/linear-static.md)

## Gentag med egne materialedata eller en ændret last

Kør fra undermappen `materialer` med `fieldcraft-cli`, `solidcraft-cli`, `bimcraft-cli` og `ft-materials` tilgængelige. Se [hele hyldeeksemplet](../README.md) for opbygning af materialedatabasen og softwareversioner.

```sh
cargo run --locked --example hyldekonsol -- --front-load-n 100
```

[Analyseopskriften](rail.json) er en gyldig FieldCraft-kommandofil med standardværdierne for det grove net. [Rust-koden](run.rs) indsætter de valgte materialetal, kraften og netstørrelsen, kører programmet og læser reaktioner, forskydninger og spændinger fra CSV. Den kontrollerer blandt andet alle knuders koordinatgrænser, endefladens placering, antal knuder og den kraft som solveren har påført. Hver kørsel bruger sin egen midlertidige mappe. Om nødvendigt kan `FIELDCRAFT_CLI` angive den absolutte sti til programmet. [Registrerede resultater fra begge net](reference.csv) · [Hent FieldCraft 0.8.1](https://github.com/tangency-labs/fieldcraft/releases/tag/v0.8.1)
