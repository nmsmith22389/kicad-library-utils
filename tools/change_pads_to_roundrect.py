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

common = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "common")
)
if common not in sys.path:
    sys.path.insert(0, common)

from print_color import PrintColor

try:
    import pcbnew
except ImportError as e:
    sys.stderr.write("    failed to import pcbnew; make sure you are running a Python version which has access to the\n"
                     "    KiCad Python Interface\n")
    raise e


def process_file(filename: str, *,
                 max_radius: float = 0.25,
                 max_rratio: float = 0.25,
                 adjust_roundrect: bool = False,
                 backup: bool = True,
                 check_only: bool = False,
                 verbose: bool = False,
                 kicad_cli: str = "",
                 upgrade: bool = True):

    changed = False
    failed = False

    if not os.path.exists(filename):
        printer.red("File does not exist: %s" % filename)
        return

    if not filename.endswith(".kicad_mod"):
        printer.red("File is not a .kicad_mod : %s" % filename)
        return

    lib_name, fp_name = os.path.split(filename)
    if not lib_name:
        lib_name = '.'
    fp_name, ext = os.path.splitext(fp_name)

    try:
        module = pcbnew.FootprintLoad(lib_name, fp_name, preserveUUID=True)
    except Exception as e:
        printer.red("Could not parse footprint: %s. (%s)" % (filename, e))
        if verbose:
            # printer.red("Error: " + str(e))
            traceback.print_exc()
        return

    num_changes = 0
    for pad in module.Pads():
        pnum = pad.GetNumber()
        min_pad_diameter = min(pcbnew.ToMM(pad.GetSize()))
        max_r = min(max_radius, min_pad_diameter * max_rratio)
        rr = max_r / min_pad_diameter
        if rr != pad.GetRoundRectRadiusRatio():
            pass
        if pad.GetShape() == pcbnew.PAD_SHAPE_RECT:
            if check_only:
                if verbose:
                    printer.yellow(f"Pad {pnum} is rectangular")
            else:
                if verbose:
                    printer.green(f"Pad {pnum}: changing from rect to "
                                  f"roundrect with radius ratio {rr}")
                pad.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
                pad.SetRoundRectRadiusRatio(rr)
            num_changes += 1
        elif adjust_roundrect and pad.GetShape() == pcbnew.PAD_SHAPE_ROUNDRECT:
            current_rr = pad.GetRoundRectRadiusRatio()
            current_r = pcbnew.ToMM(pad.GetRoundRectCornerRadius())
            if current_r < 0.9999 * max_r:
                if check_only:
                    if verbose:
                        printer.yellow(f"Pad {pnum} needs to increase "
                                       f"roundrect radius ratio from "
                                       f"{current_rr:.2f} to {rr:.2f}")
                else:
                    if verbose:
                        printer.green(f"Pad {pnum}: increasing roundrect "
                                      f"radius ratio from {current_rr:.2f} to "
                                      f"{rr:.2f}")
                    pad.SetRoundRectRadiusRatio(rr)
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
            pcbnew.FootprintSave(lib_name, module)
            printer.green(f"{filename}: {num_changes} pad(s) changed")
            changed = True
        else:
            printer.green(f"{filename}: nothing changed, all pads are OK")

    return {"changed": changed, "failed": failed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Check or adjust pad shapes to roundrect with certain radius"))
    parser.add_argument("--check-only", action="store_true", help="perform only a check, do not perform any change")
    parser.add_argument("--no-backup", action="store_true", help="do not create backup files")
    parser.add_argument("--no-color", action="store_true", help="do not color output")
    parser.add_argument("--no-adjust", action="store_true", help="do not adjust existing roundrect pads")
    parser.add_argument("--verbose", "-v", action="store_true", help="create verbose output")
    parser.add_argument("--radius", type=float, default=0.25, help="define the maximum radius for the roundrect pad "
                                                                   "changes")
    parser.add_argument("--ratio", type=float, default=0.25, help="define the radius ratio for the pad changes")
    parser.add_argument("footprint", type=str, nargs='+', help="file name(s) of footprint(s) to be checked "
                                                               "and/or adjusted")
    args = parser.parse_args()

    printer = PrintColor(use_color=not args.no_color)

    summary = {"changed": 0, "failed": 0, "processed": 0}
    failed_fps = []
    for fp in args.footprint:
        retcode = process_file(fp, backup=not args.no_backup, check_only=args.check_only,
                               adjust_roundrect=not args.no_adjust, max_radius=args.radius, max_rratio=args.ratio,
                               verbose=args.verbose)
        if retcode:
            summary["processed"] += 1
            for key, val in retcode.items():
                if val:
                    summary[key] += 1
            if retcode["failed"]:
                failed_fps.append(fp)

    print(f"Processed {summary['processed']} footprint(s): {summary['changed']} changed, {summary['failed']} failed")
    if failed_fps:
        printer.red("The following footprint(s) failed:")
        printer.red("    " + ", ".join(failed_fps))
