#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Brug: $0 NY_MAPPE" >&2
    exit 2
fi

src=$(cd "$(dirname "$0")" && pwd)
mkdir -- "$1"
cd -- "$1"

solidcraft-cli run "$src/assembly.json" --param-check strict --quiet --save model.sc --out transfer.glb
bimcraft-cli run --script "$src/import.bimscript" --save model.bimc
solidcraft-cli run "$src/rail.json" --in model.sc --param-check strict --quiet --save rail.solidcraft
solidcraft-cli run "$src/export-rail.json" --in model.sc --param-check strict --quiet
solidcraft-cli snapshot --in model.sc --out model.png --width 1000 --height 680 --no-grid --no-axes \
    --camera '{"target":[150,150,12],"yaw":0.68,"pitch":-0.42,"distance":625,"fov":0.75}'
