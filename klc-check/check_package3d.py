#!/usr/bin/env python3

"""
This script checks validity of the packages3D files,
to ensure that *.stp, *.step and *.wrl files are included
in case of an addition and also that they have a
footprint file association in the official libraries.

example usage:
check_package3d.py --footprint-directory <path> --packages3d-directory <path> -mm -vv

"""

import argparse
import os
import sys


def check_model_file_ending(directory, _verbose_level):
    model = []
    model_l = []
    pckg3d_cnt = 0
    stp_cnt = 0
    step_cnt = 0
    wrl_cnt = 0
    yes_cnt = 0
    # ****************************************************************
    # Scan 3D library directory
    exclude_directories = set([".git"])
    for root_pckg3d, pckg3d_dirs, pckg3d_files in os.walk(directory):
        pckg3d_dirs[:] = [
            d for d in pckg3d_dirs if d not in exclude_directories
        ]  # exclude directory if in exclude list
        for pckg3d_file in pckg3d_files:
            # ****************************************************************
            # Check for correct file ending
            if (
                pckg3d_file.endswith(".step")
                or pckg3d_file.endswith(".stp")
                or pckg3d_file.endswith(".wrl")
            ):
                pckg3d_cnt += 1
                # ****************************************************************
                # Check for *.wrl, *.stp and *.step filenames
                # Normalize ending and count
                if pckg3d_file.endswith(".step"):
                    model = pckg3d_file.replace(".step", "")
                    step_cnt += 1
                elif pckg3d_file.endswith(".wrl"):
                    model = pckg3d_file.replace(".wrl", "")
                    wrl_cnt += 1
                elif pckg3d_file.endswith(".stp"):
                    model = pckg3d_file.replace(".stp", "")
                    stp_cnt += 1
                for i in footprint:
                    if model == footprint[i]:
                        yes_cnt += 1
                model_l.append(model)
    return model_l, step_cnt, stp_cnt, wrl_cnt, yes_cnt, pckg3d_cnt


parser = argparse.ArgumentParser(
    description=(
        "Check 3D model file type against KLC."
        "Needs a footprint library directory,"
        " and a 3D package library directory"
        " OR two filenames with *.wrl, and *.stp or *.step nameending."
    )
)
parser.add_argument(
    "--footprint-directory",
    help=(
        "Path to footprint libraries (.pretty dirs). Specify with e.g."
        ' "~/kicad/kicad-footprints/"'
    ),
)
parser.add_argument(
    "--packages3d-directory",
    help=(
        "Path to 3d model package libraries (.3dshapes dirs). Specify with e.g."
        ' "~/kicad/kicad-packages3D/"'
    ),
)
parser.add_argument(
    "-v",
    "--verbose",
    help=(
        "Screen verbose. -v Shows basic results (footprint number, 3D packages stats,"
        " 3D packages with no footprint) -vv List some of them (3d packages with no"
        " footprint) -vvv List some other of them (all 3d packages)"
    ),
    action="count",
)
parser.add_argument(
    "-m",
    "--scan-missing",
    help=(
        "Flag to scan error_missing_fp file from 3D packages repository."
        " -m to scan local and upstream file and compare"
    ),
    action="count",
)
args = parser.parse_args()
# ****************************************************************
# Check for footprint and 3d library directory
# Set the path to the directory that git clone creates.
if args.footprint_directory:
    fp_lib_path = args.footprint_directory
else:
    fp_lib_path = input("Enter fp library directory path to search in: ")
if args.packages3d_directory:
    pckg3d_lib_path = args.packages3d_directory
else:
    pckg3d_lib_path = input("Enter 3d model library directory path to search in: ")


# Absolute directory current script is in
script_dir = os.path.dirname(__file__)
common = os.path.abspath(os.path.join(script_dir, os.path.pardir, "common"))

if common not in sys.path:
    sys.path.append(common)

if args.verbose:
    verbose_level = int(args.verbose)
else:
    verbose_level = 0

if verbose_level >= 1:
    from print_color import PrintColor

    printer = PrintColor()

if os.path.isdir(fp_lib_path):
    if verbose_level >= 1:
        printer.green("Footprint folder path is correct!")
else:
    if verbose_level >= 1:
        printer.red("Footprint directory:", None, None, True)
        printer.yellow(fp_lib_path, None, None, True)
        printer.red("hasn't found.")
        printer.red("Wrong or missing footprint source directory.")
    else:
        print("Wrong or missing footprint source directory.")
    exit(1)

if os.path.isdir(pckg3d_lib_path):
    if verbose_level >= 1:
        printer.green("3d package path is correct!")
else:
    if verbose_level >= 1:
        printer.red("3D package directory:", None, None, True)
        printer.yellow(pckg3d_lib_path, None, None, True)
        printer.red("hasn't found.")
        printer.red("Wrong or missing 3D package source directory.")
    else:
        print("Wrong or missing 3D package source directory.")
    exit(1)

footprint = {}

fp_cnt = 0


errors = 0


# ****************************************************************
# Scan footprint dir
exclude_directories = set([".git"])
for root_fp, fp_dirs, fp_files in os.walk(fp_lib_path):
    # ****************************************************************
    # Count fp names remove .kicad_mod ending and keep
    fp_dirs[:] = [
        d for d in fp_dirs if d not in exclude_directories
    ]  # exclude directory if in exclude list
    for fp_file in fp_files:
        if fp_file.endswith(".kicad_mod"):
            footprint[fp_file] = fp_file.replace(".kicad_mod", "")
            fp_cnt += 1
            if verbose_level >= 4:
                print(footprint[fp_file])

if verbose_level >= 4:
    for i in footprint:
        print(footprint[i])
if verbose_level >= 1:
    printer.green("Footprints counted:", None, None, True)
    printer.yellow(str(fp_cnt))
model_list = []
(
    model_list,
    steps,
    stps,
    wrls,
    positive,
    full_3d_pckg_cnt,
) = check_model_file_ending(pckg3d_lib_path, verbose_level)

if stps + steps != wrls:
    printer.red("Condition:", None, None, True)
    printer.yellow("*.stp + *.step = *.wrl", None, None, True)
    printer.red("is not met!!")
    errors = 1
    if stps + steps > wrls:
        printer.red("Missing *.wrl file.")
    else:
        printer.red("Missing *.stp or *.step file.")
        if int(stps) == 0:
            printer.cyan("Probably *.step is the missing.")
    sys.exit(errors)
# ****************************************************************
# Remove duplicates and keep

model2 = list(dict.fromkeys(model_list))

no_link_cnt = 0

if verbose_level == 6:
    # printing the list using loop
    for x in range(len(model2)):
        print(model2[x])


if verbose_level >= 1:
    cnt_dummy = 1
    for i in range(len(model2)):
        condition = 0
        for b in footprint:
            if model2[i] == footprint[b]:
                condition = 1
                break
        if condition == 0:
            if verbose_level >= 2:
                print(cnt_dummy, ":", model2[i])
            no_link_cnt += 1
            cnt_dummy += 1

if args.scan_missing:
    local_file = open(os.path.join(pckg3d_lib_path, "error_missing_fp"), "r")
    current_missing = int(local_file.read())
    local_file.close()
    if args.scan_missing == 1:
        if no_link_cnt > current_missing:
            printer.red(
                "3D packages with no footprint are now more than they used to be."
            )
            printer.yellow("A footprint should get merged first.")
            errors = 1
        elif no_link_cnt < current_missing:
            printer.yellow(
                "3D packages with no footprint are now less than they used to be."
            )
            printer.cyan("Thank you human!")
        elif no_link_cnt == current_missing:
            printer.yellow("3D packages with no footprint were not affected.")
            printer.green("Looks like a MR can be opened now.")
            printer.cyan("Thank you human!")
    if args.scan_missing >= 2:
        import urllib.request

        try:
            f = urllib.request.urlopen(
                "https://gitlab.com/aris-kimi/kicad-packages3D/-/raw/ci_cd/error_missing_fp"
            )
            upstream_errors = f.read().decode("utf-8").split()
        except urllib.error.URLError as e:
            print(e.reason)
            printer.red(
                "An exception occurred with upstream URL. Check internet connection,"
                " firewall settings, DNS etc."
            )
            exit(1)
        printer.yellow("Upstream errors counted from file:", None, None, True)
        printer.red(str(int(upstream_errors[0])))

        printer.yellow("Currently", None, None, True)
        printer.red(str(int(upstream_errors[0])), None, None, True)
        printer.yellow("3D packages do not have a footprint file.")

        # Check our calculated missing with upstream's file named error_missing_fp.
        # If our changes are more, we should fix that, or wait.
        # If our changes are less, we should change our local counter file
        # in order to update upstream error_missing_fp counter file.
        # If our changes are the same, we shouldn't change our local counter file
        # and the script should check for that.
        if no_link_cnt > int(upstream_errors[0]):
            printer.red(
                "Looks like this MR introduces more errors than the current ones."
            )
            printer.yellow(
                "Make sure a MR is open for a review in the footprint repository and"
                " re-run this pipeline when related footprint gets merged."
            )
            errors = 1
        elif no_link_cnt < int(upstream_errors[0]):
            printer.green(
                "Looks like this MR reduced the number of errors related with missing"
                " footprints."
            )
            if no_link_cnt != current_missing:
                printer.yellow(
                    "error_missing_fp file should be edited and replace current value"
                    " with:",
                    None,
                    None,
                    True,
                )
                printer.red(str(int(upstream_errors[0])), None, None, True)
                printer.yellow("to update upstream missing footprint counter.")
                errors = 1
            else:
                printer.cyan("Thank you human.")
        elif no_link_cnt == int(upstream_errors[0]):
            if no_link_cnt != current_missing:
                printer.yellow(
                    "Looks like local error_missing_fp file's value:", None, None, True
                )
                printer.cyan(str(current_missing), None, None, True)
                printer.red("doesn't match.")
                printer.cyan(
                    "Do not worry human, but please edit the file and replace value"
                    " with:",
                    None,
                    None,
                    True,
                )
                printer.yellow(str(int(upstream_errors[0])), None, None, True)
                printer.cyan(
                    "to match with current upstream missing footprint counter."
                )
                errors = 1
            else:
                printer.green(
                    "This MR seems ready for dimensional check and further review."
                )
                printer.cyan("Thank you human.")

# ****************************************************************
# Check 3D stored name values against the footprint name values
# ****************************************************************
# Report findings as per verbosity

if verbose_level >= 1:
    printer.green("Footprints counted:", None, None, True)
    printer.yellow(str(fp_cnt), None, None, True)
if args.scan_missing:
    printer.green(
        "Local errors counted from file:", None, None, True
    )
    printer.yellow("error_missing_fp :", None, None, True)
    printer.red(str(current_missing))
print(os.linesep)
printer.green("All 3D package files mixed:", None, None, True)
printer.yellow(str(full_3d_pckg_cnt))
printer.green("*.stp files:", None, None, True)
printer.yellow(str(stps))
printer.green("*.step files:", None, None, True)
printer.yellow(str(steps))
printer.green("*.wrl files:", None, None, True)
printer.yellow(str(wrls))
printer.green("3D packages with matching footprints:", None, None, True)
printer.yellow(str(positive / 2))
printer.red("3D packages with no footprint link:", None, None, True)
printer.yellow(str(no_link_cnt))

sys.exit(errors)
