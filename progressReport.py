#! /usr/bin/env python
"""
    Search and report progress of all current running jobs by looking at the the
    RunRecord.txt file inside direct subdirectories under the given path.
"""

from sys import argv
from os import path, listdir
'''
# check for existing saved_configs.py file
if path.exists("saved_configs.py"):
    # use saved config file
    import saved_configs
    targetWorkingDirectory = saved_configs.iEbeConfigs["working_folder"]
else:
    # use CML arguments
    if len(argv)>=2:
        targetWorkingDirectory = path.abspath(argv[1])
    else:
        targetWorkingDirectory = "PlayGround"
'''
import saved_configs
resultsDir = saved_configs.iEbeConfigs["actual_results_folder"]

from subprocess import call

#print("Checking progress of events in %s:" % targetWorkingDirectory)
print("Checking progress of events in %s:" % resultsDir)
for aFolder in listdir(resultsDir):
    subFolder = path.join(resultsDir, aFolder)
    recordFile = path.join(subFolder, "RunRecord.txt")
    if not path.exists(recordFile): continue # looking at the wrong subdirectory
    print("For %s:" % aFolder)
    commandString = 'grep "events out of" RunRecord.txt | tail -n 1'
    call(commandString, shell=True, cwd=subFolder)
