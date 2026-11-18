---
name: material-model-assessment
description: Hent mængder fra Solidcraft- eller BIMcraft-modeller og beregn dokumenteret vægt, modulopdelte klimabidrag eller træets fugtbevægelse med projektets materialedatabase.
---

# Materialer fra model til dokumenteret beregning

Brug `ft-materials` fra projektroden. Rust-CLI'et skriver JSON. [Installation og datamodellen](../../../docs/RUST.md) · [Afprøvet materialevalg og elementkort](../../../examples/unified-workflow/README.md)

## Arbejdsgang

- Læs `ft-materials status`. Opret den offentlige dataudgave med `ft-materials build`, hvis den endnu ikke er installeret.
- Hent geometri med `ft-materials extract MODEL --software solidcraft` eller `--software bimcraft`. Brug `--mesh-quantities` til understøttede BIMCraft-familier. Bevar modelkontrolsum, mængdeenhed og advarsler.
- Find kandidater med `search`. Kontrollér konkret produkt, observation, betingelser og kildeversion med `lookup` og `source`. Fasthold udgavens fulde ID i projektets materialevalg.
- Brug ét godkendt materialevalg for begge programmer. Revisionskortet forbinder en bestemt CAD-krop med et bestemt BIM-element og begge modellers kontrolsummer. Se eksemplets `selection.json` og `revised/transfer.json`.
- Kør `ft-materials assess MODEL --software SOFTWARE --selection VALG.json --transfer KORT.json`. Statuskode 2 angiver et delvist resultat. Vis hvilke dele der kræver afklaring.
- En ændret kilde kan kontrolleres med `check-updates`. Brug `changes FØR EFTER --selection VALG.json` til at finde berørte dele. Bevar den tidligere udgave til eksisterende projekter.

## Afgørende fortolkning

Vægt fra volumen kræver densitet; kg/m² er ikke densitet. Brug værktøjernes enhedskonvertering. Solidcrafts totale overflade er ikke et referenceareal. Arealbaseret modelberegning kræver en eksplicit `area_basis_note`.

Klimabidrag gælder den valgte kildeindikator og livscyklusmodul. En deklaration kan være pr.1000kg eller1ton. Modul D holdes særskilt; resultater er ikke automatisk en bygnings-LCA eller dokumentation for myndighedsoverholdelse. Grundlag som `1 m² with R=1 m²K/W` kræver en yderligere metode og afvises af den simple skaleringsfunktion.

Fugtbevægelse kræver en arts-/retningsspecifik koefficient, start-/slutfugt inden for kildens interval og en eksplicit antagelse om modelakse og fiberretning. Brug ikke svind grønt→ovntørt som koefficient pr. procentpoint. Brug ikke en råtræsarts koefficient som en dokumenteret CLT-egenskab.

BIMcraft0.12.0's gulvvolumener afrundes til0,001m³. Rapporten bevarer denne usikkerhed og dens bidrag til masse/klima. Præsenter ikke resultatet med større sikkerhed end kilden eller modellen understøtter.

Resultatet skal vise model, valgte data, beregninger, enheder, kildehenvisninger, antagelser og mangler. Gem CLI’ets JSON-svar i en separat rapportfil.

## Materialefelter, levetid og drift

- Brug `ft-materials fields` til definitionerne og `coverage --material ID` for at se, hvilke felter kilden dækker. Brug derefter `facts ID --field service_life_value` eller `maintenance_frequency`. Gem værdi, sammenligningstegn, enhed, del, dokumenttype og kildested i svaret.
- Læs samme felter på modellen med `ft-materials model-facts MODEL --software SOFTWARE --selection VALG.json --transfer KORT.json --field FELT`. Et materialevalg til et opslag kræver ID, modelmaterialets navn og begrundelse. Beregningsobservationer er kun nødvendige, hvis der også skal beregnes på delen.
- Hold en producents driftsinstruks, et LCA-scenarie og en generisk middellevetid adskilt. Gengiv konkurrerende kilder med deres egne betingelser og behold usikkerhed eller manglende værdier i resultatet. Modeldata og den faktiske installation har hver deres dokumentationsgrundlag.
