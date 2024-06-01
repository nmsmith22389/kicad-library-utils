#!/usr/bin/env python3

"""
This script checks the validity of a library table against existing libraries
KiCad maintains the following default library tables:

* Symbols - sym_lib_table
* Footprints - fp_lib_table

It is important that the official libraries match the entries in these tables.

"""

import argparse
import os
import sys
from pathlib import Path
from typing import List

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from lib_table import LibTable

parser = argparse.ArgumentParser(
    description="Compare a sym-lib-table file against a list of .lib library files"
)
parser.add_argument("libs", nargs="+", help=".lib files")
parser.add_argument("-t", "--table", required=True, help="sym-lib-table file", action="store")

args = parser.parse_args()


def check_entries(lib_table: LibTable, lib_names: List[str]) -> int:

    errors = 0

    # Check for entries that are incorrectly formatted
    for entry in lib_table.entries:

        if "\\" in entry.uri:
            print(
                f"Found '\\' character in entry '{entry.name}' - Path separators must be '/'"
            )
            errors += 1

        uri_last = Path(entry.uri).stem

        if not uri_last == entry.name:
            print(f"Nickname '{entry.name}' does not match path '{entry.uri}'")
            errors += 1

    lib_table_names = [entry.name for entry in lib_table.entries]

    # Check for libraries that are in the lib_table but should not be
    for name in lib_table_names:
        if name not in lib_names:
            errors += 1
            print(f"- Extra library '{name}' found in library table")

        if lib_table_names.count(name) > 1:
            errors += 1
            print(f"- Library '{name}' is duplicated in table")

    # Check for libraries that are not in the lib_table but should be
    for name in lib_names:
        if name not in lib_table_names:
            errors += 1
            print(f"- Library '{name}' missing from library table")

    # Incorrect lines in the library table
    for error in lib_table.errors:
        errors += 1
        print("- Incorrect line found in library table:")
        print(f"  - '{error}'")

    return errors


lib_names: List[str] = []

for lib in args.libs:
    lib_name = Path(lib).stem
    lib_names.append(lib_name)

print(f"Checking library table - '{os.path.basename(args.table)}'")
print(f"Found {len(lib_names)} libraries")

table = LibTable(args.table)

errors = check_entries(table, lib_names)

sys.exit(errors)
