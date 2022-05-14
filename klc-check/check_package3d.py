#!/usr/bin/env python3

"""
This script checks validity of the packages3D files,
to ensure that both *.step and *.wrl files are included
in case of an addition and also that they have a
footprint file in the official libraries.

"""

import argparse
import os
import sys

def check_model_file_ending( directory, _verbose_level):
    model = []
    model_l = []
    pckg3d_cnt = 0
    stp_cnt = 0
    step_cnt = 0
    wrl_cnt = 0
    yes_cnt = 0
    file_count = sum(sys.getsizeof(f for f in fs if f.lower().endswith('.step')) for fs in os.walk(directory))
#****************************************************************
# Scan 3D library directory
    exclude_directories = set(['.git'])
    for root_pckg3d, pckg3d_dirs, pckg3d_files in os.walk(directory):
        pckg3d_dirs[:] = [d for d in pckg3d_dirs if d not in exclude_directories] # exclude directory if in exclude list
        for pckg3d_file in pckg3d_files:
#****************************************************************
# Check for correct file ending
            if pckg3d_file.endswith(".step") or pckg3d_file.endswith(".stp") or pckg3d_file.endswith(".wrl"):
                pckg3d_cnt += 1
#****************************************************************
# Check for *.wrl, *.stp and *.step filenames
# Normalize ending and count
                if pckg3d_file.endswith(".step"):
                    model = pckg3d_file.replace(".step", "")
                    step_cnt += 1
                    if _verbose_level >= 6:
                        print(model)
                elif pckg3d_file.endswith(".wrl"):
                    model = pckg3d_file.replace(".wrl", "")
                    wrl_cnt += 1
                    if _verbose_level >= 6:
                        print(model)
                elif pckg3d_file.endswith(".stp"):
                    model = pckg3d_file.replace(".stp", "")
                    stp_cnt += 1
                    if _verbose_level >= 6:
                        print(model)
                for i in footprint:
                    if model == footprint[i]:
                        #if _verbose_level >= 7:
                            #print("YESSSSSSSS")
                        yes_cnt += 1
                model_l.append(model)
    return model_l, step_cnt, stp_cnt, wrl_cnt, yes_cnt, pckg3d_cnt, file_count

    
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
        "Screen verbose. -v Shows basic results (footprint number, 3D packages stats, 3D packages with no footprint) -vv List some of them (3d packages with no footprint) -vvv List some other of them (all 3d packages)"
    ),
    action="count",
)
args = parser.parse_args()

#****************************************************************
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


#****************************************************************
# Scan footprint dir
exclude_directories = set(['.git'])
for root_fp, fp_dirs, fp_files in os.walk(fp_lib_path):
#****************************************************************
# Count fp names remove .kicad_mod ending and keep
    fp_dirs[:] = [d for d in fp_dirs if d not in exclude_directories] # exclude directory if in exclude list 
    for fp_file in fp_files:
        if fp_file.endswith(".kicad_mod"):
            footprint[fp_file] = fp_file.replace(".kicad_mod", "")
            fp_cnt += 1
            if verbose_level >= 2:
                print(footprint[fp_file])

if verbose_level >= 2:
    for i in footprint:
        print(footprint[i])
if verbose_level >= 1:
    print("Footprints counted:", fp_cnt)
model_list = []
model_list, steps, stps, wrls, positive, full_3d_pckg_cnt, test_file_count = check_model_file_ending(pckg3d_lib_path, verbose_level)


#****************************************************************
#Remove duplicates and keep
        
model2 = list(dict.fromkeys(model_list))
#****************************************************************
#Check 3D stored name values against the footprint name values
#****************************************************************
#Report findings as per verbosity

print("All 3D package files mixed:", full_3d_pckg_cnt)
print("*.stp files:", stps)
print("*.step files:",steps)
print("*.wrl files:",wrls)
print("3D packages with matching footprints:", positive/2, "From the function.")
#print(model2)
no_link_cnt = 0

test_cnt = 0
if verbose_level == 3:
    # printing the list using loop
    for x in range(len(model_list)):
        print(model_list[x])
    
    
if verbose_level >= 2:
    cnt_dummy = 1
    for i in range(len(model2)):
        condition = 0
        #print(model_list[i])
        for b in footprint:
            if model2[i] == footprint[b]:
                    test_cnt +=1
                    condition = 1
                    #print("HOOOOOOOOOOOOOOOOOOOOOOOP")
                    break
        if condition == 0:
            print(cnt_dummy, ":", model2[i])
            no_link_cnt += 1
            cnt_dummy += 1
#print(test_cnt)
print("3D packages with no footprint link:", no_link_cnt)
#print(no_link_cnt+test_cnt)
#print("Yeses:", positive)
#print(model2)
#print(model_list)
#print(sys.getsizeof(model_list))
#print(sys.getsizeof(model2))
#print(test_file_count)
sys.exit(errors)