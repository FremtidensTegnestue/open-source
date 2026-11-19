# BIMcraft quantity-control models

These are authored control specimens for verifying the link from a real BIMcraft model to material calculations. They are not suggested building assemblies, product certifications or design values.

`controls.bimc` contains five separate homogeneous rectangular floor specimens with explicit material assignment, across wood, concrete, steel, glass and insulation. `expected.json` records the authored millimetre dimensions and independent analytical volumes. Material names and reference record IDs are deliberately selected reference scenarios. The geometry does not establish that a particular physical product has been procured or that these are realistic floor build-ups.

| Case | Dimensions in mm | Analytical volume m3 | Element id |
| --- | --- | ---: | --- |
| Wood | 2000 × 1000 × 50 | 0.1 | 100002 |
| Concrete | 1200 × 800 × 100 | 0.096 | 100003 |
| Steel | 1000 × 500 × 10 | 0.005 | 100004 |
| Glass | 1000 × 600 × 10 | 0.006 | 100005 |
| Insulation | 1500 × 800 × 120 | 0.144 | 100006 |

The model is also exported as `controls.ifc`; reimport into BIMcraft preserves all five tested quantities and assignments in this controlled example. This is not a general round-trip guarantee for arbitrary IFC files.

## Actual CLI API

The adapter uses:

```sh
bimcraft-cli run MODEL.bimc --cmd 'inspect {}' --cmd 'elements {"limit":1000,"offset":0}'
```

The CLI emits one JSON object per line. `inspect.types` supplies type and material-layer assignments; paginated `elements` supplies stable IDs/GUIDs and actual app-computed `volume_m3`/`area_m2` values. The adapter does not calculate volumes from filenames, nominal dimensions, or the `expected.json` reference values. `inspect/elements` are read commands and no `save` is invoked by extraction. File SHA-256 is checked before and after extraction.

Lengths in these replies are mm; volume and area fields already use m3/m2. Area is category-specific (the floor's plan/net area here), not a generic facade or whole-surface area. The adapter does not silently reinterpret it as either.

## Explicit precision limitation

BIMcraft CLI 0.12.0 reports floor `volume_m3` rounded to 0.001 m3. `rounded-volume.bimc` demonstrates the loss: a 1000 × 600 × 8 mm specimen has analytical volume 0.0048 m3, while `elements` reports 0.005 m3. The adapter preserves 0.005 and emits `source_ref.volume_rounding_increment_m3 = 0.001` plus a `quantity_rounding` notice. Downstream calculations must retain this uncertainty and must not silently treat a below-resolution zero as an exact empty body.

The companion IFC export does contain the full 0.0048 `NetVolume`, but this adapter does not add a separate ad-hoc IFC parser or substitute its values. This is retained as evidence in `rounded-volume.ifc` and `rounding-regression.json`.

The adapter currently enforces the verified CLI version 0.12.0. A newer version requires rerunning controls and reviewing the quantity/precision contract before broadening support.

## Negative controls

- `missing-material.bimc`: real volume, no explicit material. The adapter returns `material_name: null` and `missing_material`; it never guesses from the type's name.
- `mixed-layers.bimc`: Timber plus Concrete. Total volume remains available, but no whole volume is attributed to either material. `material_name` remains null and `mixed_material_layers` is returned. Even a convenience row field saying `material: Concrete` must not override known mixed layers.

## Files and reproduction

`*.commands.txt` are authored model-creation scripts. `*.build.raw.jsonl` retain actual CLI creation/export replies; `*.inspect.raw.jsonl` retain the actual inspection replies. `*.extracted.json` are normalized derived records. Saved model hashes and original element records/type references accompany normalized data. Temporary generation paths appearing in historical raw replies describe where these artifacts were produced.

Run these commands from the `materialer` directory.

```sh
python3 examples/models/bimcraft/build_examples.py
python3 adapters/bimcraft.py examples/models/bimcraft/controls.bimc --out examples/models/bimcraft/rechecked.json
python3 -m unittest discover -s tests -p test_bimcraft_adapter.py -v
```

Seven tests cover real native quantities and pagination, source preservation, controlled IFC import, missing and mixed materials, absence of name guessing/geometric substitution, and the actual rounded-quantity regression.
