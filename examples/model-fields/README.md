# Hvor længe holder facadepladen i min model?

Pladen er tegnet i SolidCraft og overført til BIMCraft. Arkitekten har valgt Lindners LinCrete til den projekterede plade. Begge programmer finder de samme to kildeudsagn. Producenten angiver en beregnet levetid **over 50 år ved facadeanvendelse**. Samme dokument anfører også en nedre grænse på **mindst 50 år** med henvisning til BBSR. Det første tal har et strengt større-end-tegn, det andet tillader 50 år. Kataloget bevarer begge grænser og deres ophav. [Producentens original, PDF-side 4](https://ibudata.lca-data.com/resource/sources/d1d9893d-2d5b-44fe-a55c-151303189a64/_LinCrete_Glass-Fibre_Reinforced_Concrete_22566.pdf?version=00.01.000#page=4)

Fra projektets rod, med den offentlige v0.3-udgave installeret og modelprogrammerne i din PATH, kan du gentage opslaget.

```sh
ft-materials build
ft-materials model-facts examples/unified-workflow/revised/model.sc \
  --software solidcraft --selection examples/model-fields/selection.json \
  --transfer examples/unified-workflow/revised/transfer.json --field service_life_value

ft-materials model-facts examples/unified-workflow/revised/model.bimc \
  --software bimcraft --mesh-quantities --selection examples/model-fields/selection.json \
  --transfer examples/unified-workflow/revised/transfer.json --field service_life_value
```

I `elements[0].material_facts.records` finder du værdi, enhed, udgave, kilde og side. Prøv også `--field reaction_to_fire` for at se, hvilke ekstra materialer der indgik i den prøvede opbygning. Modelgeometrien alene dokumenterer ikke denne opbygning. Med `--field model_quantity` kan du se de mængder, programmet har aflæst på netop denne modelrevision, i `project_fields`.

En reproducerbar Rust-test slår levetid op i begge programmer med et materialevalg uden beregningsinput. Den kontrollerer også, at den fulde binding giver en masse på 25,2 kg, og at begge programmer afviser et overførselskort med forkert modelrevision.

```sh
cargo build --release --locked --bin ft-materials
cargo run --release --locked --example model-fields
```

[Resultat fra begge programmer](verification.json) · [Materialevalg](selection.json) · [Modellerne og deres mål](../unified-workflow/README.md)
