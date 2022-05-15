#!/bin/bash

# print python version
python3 -V

# clone required repos
git clone --depth 1 https://gitlab.com/kicad/libraries/kicad-footprints.git $CI_BUILDS_DIR/kicad-footprints

SCRIPT="$CI_BUILDS_DIR/kicad-library-utils/klc-check/check_package3d.py"

$SCRIPT --footprint-directory $CI_BUILDS_DIR/kicad-footprints --packages3d-directory $CI_PROJECT_DIR -vv -m