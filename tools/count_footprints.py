#! /usr/bin/python3.9

# -*- coding: utf-8 -*-

from __future__ import print_function

import fnmatch, os, sys, platform

os_var = "Windows"

if (len(sys.argv)>1):
    fp_lib_path = str(sys.argv[1])
else:
    #Set the path to the directory that git clone creates.
    fp_lib_path = input("Enter footprint library directory path to search in: ")

common = os.path.abspath(os.path.join(sys.path[0], '..','common'))

if not common in sys.path:
    sys.path.append(common)

from print_color import *
printer = PrintColor()

if os.path.isdir(fp_lib_path):
    printer.green("Folder path is correct!")
else:
    #if there are any errors, print 'fail' for these errors
    printer.red("Directory:", None, None, True)
    printer.yellow(fp_lib_path, None, None, True)
    printer.red("hasn't found.")
    printer.red("Wrong source.")
    exit(0)

fp_dir_type_ending = '.pretty'
fp_file_type_ending = '.kicad_mod'

script_dir = os.path.dirname(__file__) #Absolute directory current script is in

#Output file prefixes
fp_out_rel_path = r"output/branch_name__"
fp_out_rel_path_no_git = r"output/dir_name__"

fp_out_abs_path = os.path.join(script_dir, fp_out_rel_path)
fp_out_abs_path_no_git = os.path.join(script_dir, fp_out_rel_path_no_git)
path,folder_name = os.path.split(fp_lib_path)

try:
    import git
    from git import Repo
except ImportError:
   printer.yellow("If missing try: pip install gitpython")
   exit(0)

try:
    fp_search_repo = Repo(fp_lib_path)
    found_repo = "yes"
except git.exc.GitError:
   printer.yellow("Missing repo.")
   #exit(0)
   found_repo = "no"

if (platform.system() == os_var):
    try:
        os.mkdir(r"output")
        printer.yellow("output", None, None, True)
        printer.green("directory created.")
    except OSError as error:
        printer.yellow("output", None, None, True)
        printer.cyan("directory exists.")
        pass

if (platform.system() == os_var):
    if found_repo == "yes":
        f = open(fp_out_abs_path + fp_search_repo.active_branch.name + ".txt", 'w+')
    elif found_repo == "no":
        f = open(fp_out_abs_path_no_git + folder_name + ".txt", 'w+')

totalFiles = 0
totalDir = 0
totalTotalFiles = 0
for base, dirs, files in os.walk(fp_lib_path):
    fps_in_lib = 0
    if base.endswith(fp_dir_type_ending):
        #for directories in dirs:
        totalDir += 1
        str_list = base.replace(fp_lib_path, "")

        for file in os.listdir(base):
            # check the files which end with specific extension
            if file.endswith(fp_file_type_ending):
                # print path name of selected files, uncomment next line to verbose all footprints inside *.pretty dir.
                #print(os.path.join(r'Footprint: ', file))
                totalFiles += 1
                fps_in_lib += 1
        if (platform.system() == os_var):
            f.write("Library: " + str(str_list) + " Hosts: " + str(fps_in_lib) + " footprints." + "\n")
        print("\n")
        printer.green("Library:", None, None, True)
        printer.yellow(str(str_list))
        printer.green("Hosts:", None, None, True)
        printer.yellow(str(fps_in_lib), None, None, True)
        printer.green("footprints.", None, None, True)

    for file in os.listdir(base):
        # check the files which end with specific extension
        if file.endswith(fp_file_type_ending):
            # print path name of selected files, uncomment next line to verbose ALL footprints.
            #print(bcolors.WARNING + os.path.join(r'Footprint: ' + bcolors.OKBLUE, file))
            totalTotalFiles += 1

if (platform.system() == os_var):
    if found_repo == "yes":
        f.write('\n' + "Current active branch: " + fp_search_repo.active_branch.name)
    elif found_repo == "no":
        f.write('\n' + "Current directory: " + fp_lib_path)

    f.write("\n" + "Total Number of footprint libraries: " + str(totalDir))
    f.write("\n" + "Number of footprint files under *.pretty/ directories: " + str(totalFiles))
    #Obsolete or footprint files in non *.pretty library file
    f.write("\n" + "Obsolete footprints under non *.pretty: " + str(totalTotalFiles - totalFiles))
    f.write("\n" + "TOTAL number of footprint files: " + str(totalTotalFiles))
    f.close()
print("\n")
printer.cyan("Footprint search directory:", None, None, True)
printer.yellow(fp_lib_path)

if found_repo == "yes":
    printer.cyan("Current active branch:", None, None, True)
    printer.yellow(fp_search_repo.active_branch.name)
    if (platform.system() == os_var):
        printer.cyan("Output file directory:", None, None, True)
        printer.yellow(fp_out_abs_path + fp_search_repo.active_branch.name + ".txt")
elif found_repo == "no":
    if (platform.system() == os_var):
        printer.cyan("Output file directory:", None, None, True)
        printer.yellow(fp_out_abs_path_no_git +  folder_name + ".txt")
        
    else:
        printer.yellow("No repo found.")

print("\n", end="")
printer.cyan("Total Number of footprint libraries:", None, None, True)
printer.yellow(str(totalDir))
printer.cyan("Number of footprint files under *.pretty/ directories:", None, None, True)
printer.yellow(str(totalFiles))
#Obsolete or footprint files in non *.pretty library file
printer.yellow("Obsolete footprints under non *.pretty:", None, None, True)
printer.red(str((totalTotalFiles - totalFiles)))
printer.cyan("TOTAL number of footprint files:", None, None, True)
printer.yellow(str(totalTotalFiles))
exit(0)