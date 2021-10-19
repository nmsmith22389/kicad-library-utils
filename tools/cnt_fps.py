# -*- coding: utf-8 -*-
import fnmatch, os
#Set the path to the directory that git clone creates.
fp_lib_path = input("Enter footprint library directory path to search in : ")
fp_dir_type_ending = '.pretty'
fp_file_type_ending = '.kicad_mod'
script_dir = os.path.dirname(__file__) #Absolute directory current script is in
fp_out_rel_path = r"output\list_fp_libs_branch_"
fp_out_abs_path = os.path.join(script_dir, fp_out_rel_path)
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
try:
    from git import Repo
except ImportError:
   print("If missing try: pip install gitpython")
   exit(0)
fp_search_repo = Repo(fp_lib_path)
f = open(fp_out_abs_path + fp_search_repo.active_branch.name + ".txt", 'w')
totalFiles = 0
totalDir = 0
totalTotalFiles = 0
for base, dirs, files in os.walk(fp_lib_path):
    fps_in_lib = 0
    if base.endswith(fp_dir_type_ending):
        #for directories in dirs:
        totalDir += 1
        str_list = base.replace(fp_lib_path + "\\", "")
        for file in os.listdir(base):
            # check the files which are end with specific extension
            if file.endswith(fp_file_type_ending):
                # print path name of selected files, uncomment next line to verbose all footprints inside *.pretty dir.
                #print(os.path.join(r'Footprint: ', file))
                totalFiles += 1
                fps_in_lib += 1
        f.write("Library: " + str(str_list) + " Hosts: " + str(fps_in_lib) + " footprints." + "\n")
        print(bcolors.OKGREEN + "\nLibrary:" + bcolors.WARNING, str_list, bcolors.OKGREEN + "\nHosts:" + bcolors.WARNING, fps_in_lib, bcolors.OKGREEN + "footprints.")
    for file in os.listdir(base):
        # check the files which are end with specific extension
        if file.endswith(fp_file_type_ending):
            # print path name of selected files, uncomment next line to verbose ALL footprints.
            #print(bcolors.WARNING + os.path.join(r'Footprint: ' + bcolors.OKBLUE, file))
            totalTotalFiles += 1
f.write('\n' + "Current active branch: " + fp_search_repo.active_branch.name)
f.write("\n" + "Total Number of footprint libraries: " + str(totalDir))
f.write("\n" + "Number of footprint files under *.pretty/ directories: " + str(totalFiles))
#Obsolete or footprint files in non *.pretty library file
f.write("\n" + "Obsolete footprints under non *.pretty: " + str(totalTotalFiles - totalFiles))
f.write("\n" + "TOTAL number of footprint files: " + str(totalTotalFiles))
f.close()
print(bcolors.OKGREEN + "\n" + "Footprint search directory: " + bcolors.WARNING + fp_lib_path)
print(bcolors.OKGREEN + "Current active branch: " + bcolors.WARNING + fp_search_repo.active_branch.name)
print(bcolors.OKGREEN + "Output file directory: " + bcolors.WARNING + fp_out_abs_path + fp_search_repo.active_branch.name + ".txt")
print("\n" + bcolors.OKGREEN + "Total Number of footprint libraries:" + bcolors.WARNING, totalDir)
print(bcolors.OKGREEN + "Number of footprint files under *.pretty/ directories:" + bcolors.WARNING, totalFiles)
#Obsolete or footprint files in non *.pretty library file
print(bcolors.WARNING + "Obsolete footprints under non *.pretty:" + bcolors.FAIL, (totalTotalFiles - totalFiles))
print(bcolors.OKGREEN + "TOTAL number of footprint files:" + bcolors.WARNING, totalTotalFiles)
