#! /usr/bin/env python
"""
    This script duplicates the EBE-Node folder and generate a collection of pbs
    files to be batch-submitted. For efficiency all codes inside EBE-Node should
    be compiled.
"""

from sys import argv, exit
from os import makedirs, path, unlink
from shutil import copytree, copy, rmtree

from check_prerequisites import checkEnvironment, checkExecutables, greetings

# check argv
try:
    # set parameters
    numberOfJobs = int(argv[1])
    numberOfEventsPerJob = int(argv[2])

    # set optional parameters
    argId = 2

    argId += 1
    if len(argv)>=argId+1: # set working folder
        workingFolder = path.abspath(argv[argId])
    else:
        workingFolder = path.abspath("./PlayGround")

    argId += 1
    if len(argv)>=argId+1: # folder to store results
        resultsFolder = path.abspath(argv[argId])
    else:
        resultsFolder = path.abspath("./RESULTS")

    # CAUTION: Make sure to leave off final backslash
    resultsFolderStore = path.abspath("/store/user/palmerjh/Results")
    #resultsFolderStore = path.abspath("../iEBE_Results")

    argId += 1
    if len(argv)>=argId+1: # set wall time
        walltime = argv[argId]
    else:
        walltime = "%d:00:00" % (3*numberOfEventsPerJob) # 3 hours per job

    argId += 1
    if len(argv)>=argId+1: # whether to compress final results folder
        compressResultsFolderAnswer = argv[argId]
    else:
        compressResultsFolderAnswer = "no"
except:
    print('Usage: generateJobs.py number_of_jobs number_of_events_per_job [working_folder="./PlayGround"] [results_folder="./RESULTS"] [walltime="03:00:00" (per event)] [compress_results_folder="yes"]')
    exit()

# save config files
open("saved_configs.py", "w").writelines("""
iEbeConfigs = {
    "number_of_jobs"            :   %d,
    "number_of_events_per_job"  :   %d,
    "working_folder"            :   "%s",
    "results_folder"            :   "%s",
    "actual_results_folder"     :   "%s",
    "walltime"                  :   "%s",
    "compress_results_folder"   :   "%s",
}
""" % (numberOfJobs, numberOfEventsPerJob, workingFolder, resultsFolder, resultsFolderStore, walltime, compressResultsFolderAnswer)
)

# define colors
purple = "\033[95m"
green = "\033[92m"
blue = "\033[94m"
yellow = "\033[93m"
red = "\033[91m"
normal = "\033[0m"

# print welcome message
print(yellow)
greetings(3)
print(purple + "\n" + "-"*80 + "\n>>>>> Welcome to the event generator! <<<<<\n" + "-"*80 + normal)

# check prerequisites
print(green + "\n>>>>> Checking for required libraries <<<<<\n" + normal)
if not checkEnvironment():
    print("Prerequisites not met. Install the required library first please. Aborting.")
    exit()

# check existence of executables
print(green + "\n>>>>> Checking for existence of executables <<<<<\n" + normal)
if not checkExecutables():
    print("Not all executables can be generated. Aborting.")
    exit()

# clean up check_prerequisites.pyc
if path.exists("check_prerequisites.pyc"): unlink("check_prerequisites.pyc")

# generate events
print(green + "\n>>>>> Generating events <<<<<\n" + normal)

# prepare directories
if not path.exists(resultsFolder): makedirs(resultsFolder)
if path.exists(workingFolder): rmtree(workingFolder)
makedirs(workingFolder)

ebeNodeFolder = "EBE-Node"
crankFolderName = "crank"
crankFolder = path.join(ebeNodeFolder, crankFolderName)

# copy parameter file into the crank folder
copy("ParameterDict.py", crankFolder)

# backup parameter files to the result folder
copy(path.join(crankFolder, "SequentialEventDriver.py"), resultsFolder)
copy(path.join(crankFolder, "ParameterDict.py"), resultsFolder)

# duplicate EBE-Node folder to working directory, write .pbs file
for i in range(1, numberOfJobs+1):
    targetWorkingFolder = path.join(workingFolder, "job-%d" % i)
    targetResultsFolder = path.join(resultsFolderStore, "job-%d" % i)
    runRecord = path.join(targetResultsFolder, "RunRecord.txt")
    #runRecord = "RunRecord.txt"
    errorRecord = path.join(targetResultsFolder, "ErrorRecord.txt")
    #errorRecord = "ErrorRecord.txt"
    
    if path.exists(targetResultsFolder):
        rmtree(targetResultsFolder)
    print("DEBUG: about to make results dir")
    makedirs(targetResultsFolder)
    print("DEBUG: made results dir")

    # copy folder
    copytree(ebeNodeFolder, targetWorkingFolder)
    open(path.join(targetWorkingFolder, "job-%d.pbs" % i), "w").write(
"""#!/usr/bin/env bash
#PBS -N iEBE-%d
#PBS -l walltime=%s
#PBS -j oe
#PBS -S /bin/bash
cd %s
(cd %s
    ulimit -n 1000
    python ./SequentialEventDriver_shell.py %s %d 1> %s 2> %s
)
""" % (i, walltime, targetWorkingFolder, crankFolderName, targetResultsFolder, numberOfEventsPerJob, runRecord, errorRecord))

    if compressResultsFolderAnswer == "yes":
        open(path.join(targetWorkingFolder, "job-%d.pbs" % i), "a").write(
"""
(cd %s
    zip -r -m -q job-%d.zip job-%d
)
""" % (resultsFolderStore, i, i)
        )

    open(path.join(targetWorkingFolder, "crank/SequentialEventDriver_tmp.py"), "w").write('')
    with open(path.join(targetWorkingFolder, "crank/SequentialEventDriver.py")) as f:
        for line in f:
            open(path.join(targetWorkingFolder, "crank/SequentialEventDriver_tmp.py"), "a").write(line )

# add a data collector watcher
if compressResultsFolderAnswer == "yes":
    EbeCollectorFolder = "EbeCollector"
    utilitiesFolder = "utilities"
    watcherDirectory = path.join(workingFolder, "watcher")
    makedirs(path.join(watcherDirectory, ebeNodeFolder))
    copytree(path.join(ebeNodeFolder, EbeCollectorFolder), path.join(watcherDirectory, ebeNodeFolder, EbeCollectorFolder))
    copytree(utilitiesFolder, path.join(watcherDirectory, utilitiesFolder))
    open(path.join(watcherDirectory, "watcher.pbs"), "w").write(
"""#!/usr/bin/env bash
#PBS -N watcher
#PBS -l walltime=%s
#PBS -j oe
#PBS -S /bin/bash
cd %s
(cd %s
    python autoZippedResultsCombiner.py %s %d "job-(\d*).zip" 60 1> WatcherReport.txt
    mv WatcherReport.txt %s
)
""" % (walltime, watcherDirectory, utilitiesFolder, resultsFolder, numberOfJobs, resultsFolder)
    )

print("Jobs generated. Submit them using submitJobs scripts.")



###########################################################################
# 05-23-2013:
#   Bugfix: "cd %s" added to the pbs files.
