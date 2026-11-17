---
name: material-model-assessment
description: Hent mængder fra Solidcraft- eller BIMcraft-modeller og beregn dokumenteret vægt, modulopdelte klimabidrag eller træets fugtbevægelse med projektets materialedatabase.
---

# Materialer fra model til dokumenteret beregning

Projektroden er tre mapper over denne skillmappe og indeholder `materials.py` og `data/materials.sqlite`. Kør CLI-kommandoer fra roden. Læs [beregningsguiden](../../../docs/CALCULATIONS.md) for bindingsformat, metoder og begrænsninger.

## Arbejdsgang

- Brug `python3 materials.py extract MODEL --software solidcraft|bimcraft --out REPORT.json` til read-only udtræk. Bevar modelens checksum og advarsler.
- Brug `suggest` med samme modelargumenter til navnebaserede kandidater. Kandidater og ens navne beviser ikke produktækvivalens. Modellens standardmateriale eller manglende materialelag er ikke et valg af databasemateriale.
- Find konkrete kildeposter med `show`, `observations` og `sources`. Se enhed, metode, gyldighed og betingelser. Vælg konkrete observation-ID'er; gennemsnit ikke poster med forskellige produkter, fugtforhold eller metoder.
- Lav et bindings-JSON med modelens SHA-256, element-ID, nøjagtigt modelmaterialenavn, databasemateriale-ID, kildeobservationer og en forklaring på datavalget. Brug en tydeligt mærket referencesammenligning, når brugeren ønsker et scenarie. Hvis produkt-/materialevalget ikke kan fastslås, giv kandidater og de nødvendige afklaringer frem for et udokumenteret resultat.
- Kør `assess MODEL --software SOFTWARE --bindings BINDINGS.json --out REPORT.json` gennem `materials.py`. Exit2 betyder delvist/uafklaret resultat; læs rapporten og vis manglerne.

## Afgørende fortolkning

Vægt fra volumen kræver densitet; kg/m² er ikke densitet. Brug værktøjernes enhedskonvertering. Solidcrafts totale overflade er ikke et referenceareal. Arealbaseret modelberegning kræver en eksplicit `area_basis_note`.

Klimabidrag gælder den valgte kildeindikator og livscyklusmodul. En deklaration kan være pr.1000kg eller1ton. Modul D holdes særskilt; resultater er ikke automatisk en bygnings-LCA eller dokumentation for myndighedsoverholdelse. Grundlag som `1 m² with R=1 m²K/W` kræver en yderligere metode og afvises af den simple skaleringsfunktion.

Fugtbevægelse kræver en arts-/retningsspecifik koefficient, start-/slutfugt inden for kildens interval og en eksplicit antagelse om modelakse og fiberretning. Brug ikke svind grønt→ovntørt som koefficient pr. procentpoint. Brug ikke en råtræsarts koefficient som en dokumenteret CLT-egenskab.

BIMcraft0.12.0's gulvvolumener afrundes til0,001m³. Rapporten bevarer denne usikkerhed og dens bidrag til masse/klima. Præsenter ikke resultatet med større sikkerhed end kilden eller modellen understøtter.

Resultatet skal vise model, valgte data, beregninger, enheder, kildehenvisninger, antagelser og mangler. Brug JSON-outputfil; værktøjerne beskytter kildemodeller, inputfiler og originalarkiv mod overskrivning. Gem nye rapporter i et separat outputområde.
