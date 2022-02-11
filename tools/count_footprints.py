#! /usr/bin/python3.9
# -*- coding: utf-8 -*-
import fnmatch, os, sys, platform

os_var = "Windows"

if (len(sys.argv)>1):
    fp_lib_path = str(sys.argv[1])
else:
    #Set the path to the directory that git clone creates.
    fp_lib_path = input("Enter footprint library directory path to search in: ")
try:
    from colorama import init, Fore, Back, Style
except ImportError:
   print("If missing try: pip install colorama")
   exit(0)
#The colours of the things
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
init() #init() function to enable text coloring

if os.path.isdir(fp_lib_path):
    print(bcolors.OKGREEN + "Folder path is correct!")
else:
    #if there are any errors, print 'fail' for these errors
    print(bcolors.FAIL + "Directory:", bcolors.WARNING + fp_lib_path, bcolors.FAIL + "hasn't found.")
    print(bcolors.FAIL + "Wrong source.")
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
   print("If missing try: pip install gitpython")
   exit(0)

try:
    fp_search_repo = Repo(fp_lib_path)
    found_repo = "yes"
except git.exc.GitError:
   print(bcolors.FAIL + "Missing repo." + bcolors.WARNING)
   #exit(0)
   found_repo = "no"

if (platform.system() == os_var):
    try:
        os.mkdir(r"output")
        print(bcolors.WARNING + "output" + bcolors.OKGREEN + " directory created.")
    except OSError as error:
        print(bcolors.WARNING + "output" + bcolors.FAIL + " directory exists.")
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
        print(bcolors.OKGREEN + "\nLibrary:" + bcolors.WARNING, str_list, bcolors.OKGREEN + "\nHosts:" + bcolors.WARNING, fps_in_lib, bcolors.OKGREEN + "footprints.")
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
print(bcolors.OKGREEN + "\n" + "Footprint search directory: " + bcolors.WARNING + fp_lib_path)

if found_repo == "yes":
    print(bcolors.OKGREEN + "Current active branch: " + bcolors.WARNING + fp_search_repo.active_branch.name)
    if (platform.system() == os_var):
        print(bcolors.OKGREEN + "Output file directory: " + bcolors.WARNING + fp_out_abs_path + fp_search_repo.active_branch.name + ".txt")
elif found_repo == "no":
    if (platform.system() == os_var):
        print(bcolors.OKGREEN + "Output file directory: " + bcolors.WARNING + fp_out_abs_path_no_git +  folder_name + ".txt")
    else:
        print(bcolors.WARNING + "No repo found.")

print("\n" + bcolors.OKGREEN + "Total Number of footprint libraries:" + bcolors.WARNING, totalDir)
print(bcolors.OKGREEN + "Number of footprint files under *.pretty/ directories:" + bcolors.WARNING, totalFiles)
#Obsolete or footprint files in non *.pretty library file
print(bcolors.WARNING + "Obsolete footprints under non *.pretty:" + bcolors.FAIL, (totalTotalFiles - totalFiles))
print(bcolors.OKGREEN + "TOTAL number of footprint files:" + bcolors.WARNING, totalTotalFiles)
exit(0)