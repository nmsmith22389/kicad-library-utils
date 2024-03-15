#!/usr/bin/env bash
set -e

source $(dirname ${BASH_SOURCE[0]})/common.sh

CHANGES=$(git diff-tree --diff-filter=AMR --no-commit-id --name-only -r "$BASE_SHA" "$TARGET_SHA")
mkdir -p "$CI_BUILDS_DIR/tmp"
mkdir -p screenshots
mkdir -p "$HOME/.config/kicad/8.99/"
cp "$CI_BUILDS_DIR/kicad-library-utils/scripts/3d_viewer.json" "$HOME/.config/kicad/8.99/3d_viewer.json"

for change in $CHANGES; do
    if [[ $change =~ .*\.kicad_mod ]]; then
        modelname=$(echo "/$CI_BUILDS_DIR/kicad-packages3D/$change" |sed -e "s/.pretty/.3dshapes/;s/.kicad_mod//")
        echo "Creating a board with footprint: $change"
        python3 "$CI_BUILDS_DIR/kicad-library-utils/scripts/create_model_board.py" -f "/$CI_PROJECT_DIR/$change" -w "$modelname.wrl" -s "$modelname.step" \
            "$CI_BUILDS_DIR/tmp/board.kicad_pcb"
        echo "Exporting png"
        kicad-cli pcb render --width 2000 --height 2000 --rotate 0,0,0 --perspective --quality user \
            -o "screenshots/$change.png" "$CI_BUILDS_DIR/tmp/board.kicad_pcb"
    fi
done
