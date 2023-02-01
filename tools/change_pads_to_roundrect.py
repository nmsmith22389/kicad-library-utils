#!/usr/bin/env python3

"""
This script checks rectangular and roundrect pads in a footprint and adjusts
rect and roundrect pads to roundrect with a specified radius ratio/radius.

Run
    change_pads_to_roundrect.py --help

for usage information.
"""

import argparse
import os
import shutil
import sys
import traceback
import subprocess
import tempfile

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from kicad_mod import KicadMod
from print_color import PrintColor


def process_file(filename: str, *,
                 max_radius: float = 0.25,
                 max_rratio: float = 0.25,
                 adjust_roundrect: bool = False,
                 backup: bool = True,
                 check_only: bool = False,
                 verbose: bool = False,
                 kicad_cli: str = "",
                 upgrade: bool = True):

    if not os.path.exists(filename):
        printer.red("File does not exist: %s" % filename)
        return

    if not filename.endswith(".kicad_mod"):
        printer.red("File is not a .kicad_mod : %s" % filename)
        return

    try:
        module = KicadMod(filename)
    except Exception as e:
        printer.red("Could not parse footprint: %s. (%s)" % (filename, e))
        if verbose:
            # printer.red("Error: " + str(e))
            traceback.print_exc()
        return

    file_version = module.version

    num_changes = 0
    for pad in module.pads:
        pname = pad["number"]
        min_pad_diameter = min(pad["size"]["x"], pad["size"]["y"])
        max_r = min(max_radius, min_pad_diameter * max_rratio)
        rr = max_r / min_pad_diameter
        if pad["shape"] == "rect":
            if check_only:
                if verbose:
                    printer.yellow(f"Pad {pname} is rectangular")
            else:
                if verbose:
                    printer.green(f"Pad {pname}: changing from rect to "
                                  f"roundrect with radius ratio {rr}")
                pad.update(shape="roundrect", roundrect_rratio=rr)
            num_changes += 1
        elif adjust_roundrect and pad["shape"] == "roundrect":
            current_rr = pad.get("roundrect_rratio", 0)
            current_r = min_pad_diameter * current_rr
            if current_r < max_r:
                if check_only:
                    if verbose:
                        printer.yellow(f"Pad {pname} needs to increase "
                                       f"roundrect radius ratio from "
                                       f"{current_rr:.2f} to {rr:.2f}")
                else:
                    if verbose:
                        printer.green(f"Pad {pname}: increasing roundrect "
                                      f"radius ratio from {current_rr:.2f} to "
                                      f"{rr:.2f}")
                    pad.update(roundrect_rratio=rr)
                num_changes += 1

    if check_only:
        if num_changes:
            printer.red(f"{filename}: {num_changes} pad(s) need adjustment")
        else:
            printer.green(f"{filename}: all pads are OK")
    else:
        if num_changes > 0:
            if backup:
                shutil.copy(filename, filename + ".bak")
            module.save(filename)
            printer.green(f"{filename}: {num_changes} pad(s) changed")
            if upgrade and file_version != KicadMod.SEXPR_BOARD_FILE_VERSION:
                tmpdir = None
                tmpfile = None
                try:
                    tmpdir = tempfile.mkdtemp()
                    tmpfile = os.path.join(tmpdir, os.path.split(filename)[1])
                    shutil.copy(filename, tmpdir)
                    subprocess.run([kicad_cli, 'fp', 'upgrade', tmpdir], check=True, capture_output=True)
                    shutil.move(tmpfile, filename)
                    printer.green(f"{filename}: was upgraded to latest file format using kicad-cli")
                except FileNotFoundError:
                    printer.yellow("Cannot find kicad-cli; footprint can not be converted to the latest file format.")
                finally:
                    if tmpfile and os.path.exists(tmpfile):
                        os.unlink(tmpfile)
                    if tmpdir and os.path.exists(tmpdir):
                        os.rmdir(tmpdir)
        else:
            printer.green(f"{filename}: nothing changed, all pads are OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Check or adjust pad shapes to roundrect with certain radius"))
    parser.add_argument("--check-only", action="store_true", help="perform only a check, do not perform any change")
    parser.add_argument("--no-backup", action="store_true", help="do not create backup files")
    parser.add_argument("--no-color", action="store_true", help="do not color output")
    parser.add_argument("--no-adjust", action="store_true", help="do not adjust existing roundrect pads")
    parser.add_argument("--no-upgrade", action="store_true", help="skip upgrade file to latest format using kicad-cli")
    parser.add_argument("--kicad-cli", type=str, default="", metavar="PATH",
                        help="specify path to kicad-cli for file format upgrade; default is 'kicad-cli' or the "
                             "contents of the environment variable 'KICAD_CLI' (if defined)")
    parser.add_argument("--verbose", "-v", action="store_true", help="create verbose output")
    parser.add_argument("--radius", type=float, default=0.25, help="define the maximum radius for the roundrect pad "
                                                                   "changes")
    parser.add_argument("--ratio", type=float, default=0.25, help="define the radius ratio for the pad changes")
    parser.add_argument("footprint", type=str, nargs='+', help="file name(s) of footprint(s) to be checked "
                                                               "and/or adjusted")
    args = parser.parse_args()

    printer = PrintColor(use_color=not args.no_color)

    kicad_cli = args.kicad_cli if args.kicad_cli else os.environ.get('KICAD_CLI', 'kicad-cli')

    for fp in args.footprint:
        process_file(fp, backup=not args.no_backup, check_only=args.check_only, adjust_roundrect=not args.no_adjust,
                     max_radius=args.radius, max_rratio=args.ratio, verbose=args.verbose,
                     kicad_cli=kicad_cli, upgrade=not args.no_upgrade)
