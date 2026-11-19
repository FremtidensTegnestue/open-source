# Solidcraft quantity controls

These are actual Solidcraft 0.44.0 model files, authored through `solidcraft-cli`. Each represents an abstract homogeneous rectangular solid with an explicitly named material. They test the model-to-data chain, not the construction suitability of a real assembly.

| Control | Explicit material scenario | Dimensions, mm | Analytic volume, m³ |
| --- | --- | --- | ---: |
| `solid-wood.sc` | CLT, BR18 B1318 | 1000 × 500 × 100 | 0.05 |
| `solid-concrete.sc` | C25/30 factory concrete, BR18 B1433 | 2000 × 300 × 200 | 0.12 |
| `solid-steel.sc` | Rolled structural steel, BR18 D1591 | 800 × 100 × 20 | 0.0016 |
| `solid-glass.sc` | Glass blocks, BR18 G0954 | 1200 × 800 × 8 | 0.00768 |
| `solid-insulation.sc` | EPS fill, BR18 G0161 | 1500 × 600 × 150 | 0.135 |
| `solid-wood-moisture.sc` | White fir (`Fir, white`) species scenario | 232 × 20 × 10 | 0.0000464 |

The last specimen supports a separately requested moisture calculation. Its 232 mm X extent is *explicitly selected by the calculation request* as tangential width; neither the adapter nor its bounding box establishes grain direction. White fir is separate from CLT and its species coefficient must not automatically be applied to CLT.

`unknown.sc` is a 100 mm cube without a material assignment. Solidcraft reports a `Default` material and synthetic default density for it. The adapter returns `material_name = null` and a `material_unspecified` warning, preserving that default only in raw provenance.

## Extraction

```sh
python3 adapters/solidcraft.py examples/models/solidcraft/solid-wood.sc --out /tmp/wood-quantities.json
```

The adapter runs the actual `solidcraft-cli eval MODEL.sc` command. Its closed-body `volume_mm3` is computed by the geometry engine, then divided by 1,000,000,000 to obtain m³. It never computes volume by multiplying the bounding-box extents. `source_ref.raw_measurement` and `extraction.raw_reply` preserve the CLI's measured output and assigned material name. The original model's SHA-256 is checked before and after extraction.

The CLI also returns total body surface area. It is exposed as `surface_area_m2`; `area_m2` remains unknown because a total surface is not a facade, projected, or EPD reference area. `dimensions_m` contains world-axis-aligned bounding-box X/Y/Z extents and is labelled accordingly. No material axis or grain direction is inferred.

The material densities authored in the models are display/model attributes only. Database calculations must choose and cite their own observations; the adapter does not use app mass/density to bypass missing database data.

Supported inert files are `.sc`, `.step`, and `.stp`. Script JSON is rejected because the same Solidcraft interface can execute it. STEP files without material assignment remain unspecified. Failed timeline features cause extraction to fail; unavailable closed-body volumes remain null with a warning.

## Artifacts and reproduction

- `*.commands.json`: source command scripts to create each model.
- `*.sc`: actual saved Solidcraft projects.
- `*.creation-reply.json`: source model-creation replies.
- `*.eval.json`: actual raw read-only geometric measurements.
- `*.normalized.json`: adapter output, including source-model hash.
- `expected.json`: independent dimensional/analytical controls.
- `solid-wood.png`: actual CLI snapshot, visually inspected after rendering.

```sh
python3 examples/models/solidcraft/build_examples.py
python3 -m unittest discover -s tests -p test_solidcraft_adapter.py -v
```

No geometrical or material-data certification is implied by matching these analytic controls. The adapter supports measured solids, including measurements of more complicated geometry; source-specific interpretation of quantity and material remains explicit.
