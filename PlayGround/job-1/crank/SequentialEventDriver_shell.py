#!/usr/bin/env python

from sys import argv, exit
try:
    resultsFolder = argv[1]
    numberOfEvents = int(argv[2])
except:
    print("Usage: SequentialEventDriver_shell.py results_folder_for_job number_of_events")
    exit()

# call the real shell
import SequentialEventDriver
SequentialEventDriver.controlParameterList["resultDir"] = resultsFolder
SequentialEventDriver.controlParameterList["numberOfEvents"] = numberOfEvents
SequentialEventDriver.sequentialEventDriverShell()
