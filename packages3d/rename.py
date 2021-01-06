#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import sys, os
import re
import json
import ntpath
import glob

parser = argparse.ArgumentParser(description="Check symbols for footprint errors")

parser.add_argument('-l', '--lib', nargs='+', help='3d model libraries (.3dshapes files)', action='store')
parser.add_argument('-r', '--replace', help='Path to JSON file containing replacement information')
parser.add_argument('-v', '--verbose', help='Verbosity level', action='count')
parser.add_argument('--real', help='Run it for real', action='store_true')

args = parser.parse_args()

if not args.verbose:
    args.verbose = 0

verbose = args.verbose

if args.replace:
    with open(args.replace) as json_file:
        replacements = json.loads(json_file.read())

else:
    replacements = {}

KEYS = ['library', 'footprint', 'prefix', "replace"]

# Ensure correct keys
for key in KEYS:
    if not key in replacements:
        replacements[key] = {}

for lib in args.lib:
    if not lib.endswith(os.sep):
        lib += os.sep

    #print(glob.glob('{:}*.kicad_mod'.format(lib)))
    for model_path in glob.glob('{:s}*.wrl'.format(lib)):
        model_name = ntpath.basename(model_path)
        model_name = os.path.splitext(model_name)[0]

        if model_name in replacements['footprint']:
            print("{:s} -> {:s}".format(model_name, replacements['footprint'][model_name]))
            if args.real:
                os.rename("{:s}{:s}.wrl".format(lib,model_name),
                    "{:s}{:s}.wrl".format(lib,replacements['footprint'][model_name]))
                os.rename("{:s}{:s}.step".format(lib,model_name),
                    "{:s}{:s}.step".format(lib,replacements['footprint'][model_name]))
