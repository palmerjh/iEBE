#! /usr/bin/env python
# This package performs a sequential calculations of a given number of events,
# after reading parameters from ParameterDict.py. The most important control
# parameters are set in controlParameterList, for other parameters see
# allParameterLists. This package is intended to be working-at-background thus
# only basic output are generated. When necessary, other functions given in the
# package for single executables can be invoked individually for more
# flexibilities.
# The main entry is the sequentialEventDriverShell function.

from os import path, getcwd, remove, makedirs
from sys import stdout
import sys
sys.path.insert(0, path.abspath('../../../..'))
from saved_configs import iEbeConfigs
from shutil import move, copy, rmtree
from glob import glob
from subprocess import call
import numpy as np

class ExecutionError(Exception): pass # used to signal my own exception

# set global default parameters
allParameterLists = [
    'controlParameterList',
    'centralityParameters',
    'superMCControl',
    'superMCParameters',
    'hydroControl',
    'hydroParameters',
    'iSSControl',
    'iSSParameters',
    'iSControl',
    'iSParameters',
    'osc2uControl',
    'osc2uParameters',
    'urqmdControl',
    'urqmdParameters',
    'binUtilitiesControl',
    'binUtilitiesParameters',
]

controlParameterList = {
    'simulation_type'       :   'hybrid', # 'hybrid' or 'hydro'
    'niceness'              :   10,       # range from 0 to 19 for process priority, 0 for the highest priority
    'numberOfEvents'        :   10, # how many sequential calculations
    'rootDir'               :   path.abspath('../'),
    'resultDir'             :   path.abspath('placeholder/'), # final results will be saved here, absolute
    'eventResultDirPattern' :   'event-%d', # %d->event_id, where event results are saved
    'eventResultDir'        :   None, # used to pass event result folder from sequentialEventDriverShell to others
    'combinedUrqmdFile'     :   'urqmdCombined.txt', # urqmd from all events will be combined into this file
    'buildCMD'              :   'make build',
    'cleanCMD'              :   'make clean',
}

centralityParameters = {
    'centrality': '0-5%',  # centrality bin
    'cut_type': 'total_entropy',
    # centrality cut variable: total_entropy or Npart
}
superMCControl = {
    'mainDir'                       :   'superMC',
    'dataDir'                       :   'data', # where initial conditions are stored, relative
    'dataFiles'                     :   '*event*.dat', # data filenames
    'numberOfEventsParameterName'   :   'nev',
    'executable'                    :   'superMC.e',
}
superMCParameters = {
    'which_mc_model'                :   5,
    'sub_model'                     :   1,
    'Npmin'                         :   0,
    'Npmax'                         :   1000,
    'bmin'                          :   0,
    'bmax'                          :   20,
    'cutdSdy'                       :   1,
    'cutdSdy_lowerBound'            :   551.864,
    'cutdSdy_upperBound'            :   1000000.0,
    'Aproj'                         :   208,
    'Atarg'                         :   208,
    'ecm'                           :   2760,
    'finalFactor'                   :   56.763,
    'use_ed'                        :   0,
    'alpha'                         :   0.118,
    'lambda'                        :   0.288,
    'operation'                     :   1,
    'cc_fluctuation_model'          :   6,
}

hydroControl = {
    'mainDir'               :   'VISHNew',
    'initialConditionDir'   :   'Initial', # hydro initial condition folder, relative
    'initialConditionFile'  :   'InitialSd.dat', # IC filename
    'resultDir'             :   'results', # hydro results folder, relative
    'resultFiles'           :   '*.dat', # results files
    'saveICFile'            :   True, # whether to save initial condition file
    'saveResultGlobs'       :   ['surface.dat', 'dec*.dat', 'ecc*.dat'], # files match these globs will be saved
    'executable'            :   'VISHNew.e',
}
hydroParameters = {
    'IINIT'     :   2,
    'IEOS'      :   7,
    'iEin'      :   1,
    'vis'       :   0.08,
    'iLS'       :   130,
    'T0'        :   0.6, # tau_0
    'Edec'      :   0.3, # 0.3->160 MeV, 0.18->120 MeV
    'factor'    :   1.0
}

iSSControl = {
    'mainDir'           :   'iSS',
    'operationDir'      :   'results',
    'saveResultGlobs'   :   ['*vn*.dat'], # files in the operation directory matching these globs will be saved
    'OSCARFile'         :   'OSCAR.DAT',
    'executable'        :   'iSS.e',
}
iSSParameters = {
    'calculate_vn'                  :   0,
    'MC_sampling'                   :   2,
    'number_of_repeated_sampling'   :   10,
    'y_LB'                          :   -2.5,
    'y_RB'                          :   2.5,
}

iSControl = {
    'mainDir'           :   'iS',
    'operationDir'      :   'results',
    'saveResultGlobs'   :   ['dN_ptdptdphidy.dat', '*_vndata.dat', 'v2data*'], # files in the operation directory matching these globs will be saved
    'executables'       :   ('iS.e', 'resonance.e', 'iInteSp.e'),
    'entryShell'        :   'iS_withResonance.sh',
}
iSParameters = {}

osc2uControl = {
    'mainDir'           :   'osc2u',
    'outputFilename'    :   'fort.14',
    'saveOSCAR'         :   True, # whether to save OSCAR file
    'executable'        :   'osc2u.e',
}
osc2uParameters = {}

urqmdControl = {
    'mainDir'           :   'urqmd',
    'controlFilename'   :   'uqmd.burner',
    'ICFilename'        :   'OSCAR.input',
    'outputFilename'    :   'particle_list.dat',
    'saveOutputFile'    :   True, # whether to save the output file
    'executable'        :   'urqmd.e',
    'entryShell'        :   'runqmd.sh',
}
urqmdParameters = {}

binUtilitiesControl = {
    'mainDir'               :   'binUtilities',
    'operationDir'          :   'results',
    'saveResultGlobs'       :   ['*flow*.dat', 'pT_*.dat'], # files in the operation directory matching these globs will be saved
    'executable'            :   'urqmdBinShell.py',
}
binUtilitiesParameters = {}

EbeCollectorControl = {
    'mainDir'               :   'EbeCollector',
    'executable_hybrid'     :   'EbeCollectorShell_hydroWithUrQMD.py',
    'executable_hydro'      :   'EbeCollectorShell_pureHydro.py',
}
EbeCollectorParameters = {
    'subfolderPattern'      :   '"event-(\d*)"',
    'databaseFilename'      :   'collected.db',
}

def readInParameters():
    """ Overwrite default parameter lists with those in ParameterDict. """
    try:
        import ParameterDict
        for aParameterList in allParameterLists:
            if aParameterList in dir(ParameterDict):
                exec("%s.update(ParameterDict.%s)" % (aParameterList, aParameterList))
    except (IOError, SyntaxError):
        raise ExecutionError("Errors trying to open/read the ParameterDict.py file!")


def translate_centrality_cut():
    """
    translate the centrality boundaries to Npart, dS/dy, b values and update
    the parameter lists for simulations
    """
    cut_type = centralityParameters['cut_type']
    if cut_type not in ['total_entropy', 'Npart']:
        print "invalid centrality cut type: ", cut_type
        exit(1)

    centrality_string = centralityParameters['centrality']
    centrality_lower_bound = float(centrality_string.split('-')[0])
    centrality_upper_bound = float(
        centrality_string.split('-')[1].split('%')[0])

    if superMCParameters['which_mc_model'] == 5:
        model_name = 'MCGlb'
    elif superMCParameters['which_mc_model'] == 1:
        model_name = 'MCKLN'

    if superMCParameters['cc_fluctuation_model'] != 0:
        multiplicity_fluctuation = 'withMultFluct'
    else:
        multiplicity_fluctuation = 'noMultFluct'

    collision_energy = str(superMCParameters['ecm'])

    Aproj = superMCParameters['Aproj']
    Atrag = superMCParameters['Atarg']
    nucleus_name_dict = {
        208: 'Pb',
        197: 'Au',
        238: 'U',
        63: 'Cu',
        1: 'p',
        2: 'd',
        3: 'He',
    }
    if Aproj == Atrag:  #symmetric collision
        nucleus_name = nucleus_name_dict[Aproj]+nucleus_name_dict[Atrag]
    else:  # asymmetric collision
        nucleus_name = (nucleus_name_dict[min(Aproj, Atrag)]
                        + nucleus_name_dict[max(Aproj, Atrag)])

    centrality_cut_file_name = (
        'iebe_centralityCut_%s_%s_sigmaNN_gauss_d0.9_%s.dat'
        % (cut_type, model_name + nucleus_name + collision_energy,
           multiplicity_fluctuation)
    )

    try:
        centrality_cut_file = np.loadtxt(
            path.join(path.abspath('../centrality_cut_tables'),
                      centrality_cut_file_name))
    except IOError:
        print "Can not find the centrality cut table for the collision system"
        print centrality_cut_file_name
        exit(1)

    lower_idx = (
        centrality_cut_file[:, 0].searchsorted(centrality_lower_bound+1e-30))
    upper_idx = (
        centrality_cut_file[:, 0].searchsorted(centrality_upper_bound))

    cut_value_upper = (
        (centrality_cut_file[lower_idx-1, 1]
         - centrality_cut_file[lower_idx, 1])
        /(centrality_cut_file[lower_idx-1, 0]
          - centrality_cut_file[lower_idx, 0])
        *(centrality_lower_bound - centrality_cut_file[lower_idx-1, 0])
        + centrality_cut_file[lower_idx-1, 1]
    )
    cut_value_low = (
        (centrality_cut_file[upper_idx-1, 1]
         - centrality_cut_file[upper_idx, 1])
        /(centrality_cut_file[upper_idx-1, 0]
          - centrality_cut_file[upper_idx, 0])
        *(centrality_upper_bound - centrality_cut_file[upper_idx-1, 0])
        + centrality_cut_file[upper_idx-1, 1]
    )
    if cut_type == 'total_entropy':
        superMCParameters['cutdSdy'] = 1
        npart_min = min(centrality_cut_file[lower_idx-1:upper_idx+1, 2])
        npart_max = max(centrality_cut_file[lower_idx-1:upper_idx+1, 3])
        b_min = min(centrality_cut_file[lower_idx-1:upper_idx+1, 4])
        b_max = max(centrality_cut_file[lower_idx-1:upper_idx+1, 5])
        superMCParameters['cutdSdy_lowerBound'] = cut_value_low
        superMCParameters['cutdSdy_upperBound'] = cut_value_upper
    elif cut_type == 'Npart':
        superMCParameters['cutdSdy'] = 0
        b_min = min(centrality_cut_file[lower_idx-1:upper_idx+1, 4])
        b_max = max(centrality_cut_file[lower_idx-1:upper_idx+1, 5])
    superMCParameters['Npmax'] = npart_max
    superMCParameters['Npmin'] = npart_min
    superMCParameters['bmax'] = b_max
    superMCParameters['bmin'] = b_min

    #print out information
    print '-'*80
    print('%s collisions at sqrt{s} = %s A GeV with %s initial conditions'
          % (nucleus_name , collision_energy, model_name))
    print("Centrality : %g - %g"
          % (centrality_lower_bound, centrality_upper_bound) + r"%")
    print 'centrality cut on ', cut_type
    if cut_type == 'total_entropy':
        print 'dS/dy :', cut_value_low, '-', cut_value_upper
    print "Npart: ", npart_min, '-', npart_max
    print "b: ", b_min, '-', b_max, ' fm'
    print '-'*80
    return


def generateSuperMCInitialConditions(numberOfEvents):
    """
        Generate initial conditions using superMC. It then yield the absolute
        path for all the initial conditions.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    superMCDirectory = path.join(controlParameterList['rootDir'], superMCControl['mainDir'])
    superMCDataDirectory = path.join(superMCDirectory, superMCControl['dataDir'])
    superMCExecutable = superMCControl['executable']

    # clean up the data subfolder for output
    cleanUpFolder(superMCDataDirectory)

    # check executable
    checkExistenceOfExecutable(path.join(superMCDirectory, superMCExecutable))

    # set "nev=#" in superMCParameters
    superMCParameters[superMCControl['numberOfEventsParameterName']] = numberOfEvents
    # form assignment string
    assignments = formAssignmentStringFromDict(superMCParameters)
    # form executable string
    executableString = "nice -n %d ./" % (ProcessNiceness) + superMCExecutable + assignments
    # execute!
    run(executableString, cwd=superMCDirectory)

    # yield initial conditions
    for aFile in glob(path.join(superMCDataDirectory, superMCControl['dataFiles'])):
        # then yield it
        yield path.join(superMCDataDirectory, aFile)


def hydroWithInitialCondition(aFile):
    """
        Perform a single hydro calculation with the given absolute path to an
        initial condition. Yield the result files.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    hydroDirectory = path.join(controlParameterList['rootDir'], hydroControl['mainDir'])
    hydroICDirectory = path.join(hydroDirectory, hydroControl['initialConditionDir'])
    hydroResultsDirectory = path.join(hydroDirectory, hydroControl['resultDir'])
    hydroExecutable = hydroControl['executable']

    # check executable
    checkExistenceOfExecutable(path.join(hydroDirectory, hydroExecutable))

    # clean up initial and results folder
    cleanUpFolder(hydroICDirectory)
    cleanUpFolder(hydroResultsDirectory)

    # check existence of the initial conditions
    if not path.exists(aFile):
        raise ExecutionError("Hydro initial condition file %s not found!" % aFile)

    # storing initial condition file
    if hydroControl['saveICFile']:
        copy(aFile, controlParameterList['eventResultDir'])

    # move initial condition to the designated folder
    move(aFile, path.join(hydroICDirectory, hydroControl['initialConditionFile']))

    # form assignment string
    assignments = formAssignmentStringFromDict(hydroParameters)
    # form executable string
    executableString = "nice -n %d ./" % (ProcessNiceness) + hydroExecutable + assignments
    # execute!
    run(executableString, cwd=hydroDirectory)

    # yield result files
    worthStoring = []
    for aGlob in hydroControl['saveResultGlobs']:
        worthStoring.extend(glob(path.join(hydroResultsDirectory, aGlob)))
    for aFile in glob(path.join(hydroResultsDirectory, hydroControl['resultFiles'])):
        # check if this file worth storing, then copy to event result folder
        if aFile in worthStoring:
            copy(aFile, controlParameterList['eventResultDir'])
        # yield it
        yield path.join(hydroResultsDirectory, aFile)


def iSSWithHydroResultFiles(fileList):
    """
        Perform iSS calculation using the given list of hydro result files.
        Return the path to the OSCAR file.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    iSSDirectory = path.join(controlParameterList['rootDir'], iSSControl['mainDir'])
    iSSOperationDirectory = path.join(iSSDirectory, iSSControl['operationDir']) # for both input & output
    iSSOSCARFilepath = path.join(iSSDirectory, iSSControl['OSCARFile'])
    iSSExecutable = iSSControl['executable']

    # check executable
    checkExistenceOfExecutable(path.join(iSSDirectory, iSSExecutable))

    # clean up operation folder
    cleanUpFolder(iSSOperationDirectory)

    # check existence of hydro result files and move them to operation folder
    for aFile in fileList:
        if not path.exists(aFile):
            raise ExecutionError("Hydro result file %s not found!" % aFile)
        else:
            move(aFile, iSSOperationDirectory)

    # form assignment string
    assignments = formAssignmentStringFromDict(iSSParameters)
    # form executable string
    executableString = "nice -n %d ./" % (ProcessNiceness) + iSSExecutable + assignments
    # execute!
    run(executableString, cwd=iSSDirectory)

    # save some of the important result files
    worthStoring = []
    for aGlob in iSSControl['saveResultGlobs']:
        worthStoring.extend(glob(path.join(iSSOperationDirectory, aGlob)))
    for aFile in glob(path.join(iSSOperationDirectory, "*")):
        if aFile in worthStoring:
            move(aFile, controlParameterList['eventResultDir'])

    # return OSCAR file path
    return iSSOSCARFilepath


def iSWithResonancesWithHydroResultFiles(fileList):
    """
        Perform iS calculation using the given list of hydro result files,
        followed by resonance calculations and iInteSp calculations.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    iSDirectory = path.join(controlParameterList['rootDir'], iSControl['mainDir'])
    iSOperationDirectory = path.join(iSDirectory, iSControl['operationDir']) # for both input & output
    iSExecutables = iSControl['executables']
    iSExecutionEntry = iSControl['entryShell']

    # check executable
    checkExistenceOfExecutables([path.join(iSDirectory, aExe) for aExe in iSExecutables])

    # clean up operation folder
    cleanUpFolder(iSOperationDirectory)

    # check existence of hydro result files and move them to operation folder
    for aFile in fileList:
        if not path.exists(aFile):
            raise ExecutionError("Hydro result file %s not found!" % aFile)
        else:
            move(aFile, iSOperationDirectory)

    # execute!
    run("nice -n %d bash ./" % (ProcessNiceness) + iSExecutionEntry, cwd=iSDirectory)

    # save some of the important result files
    worthStoring = []
    for aGlob in iSControl['saveResultGlobs']:
        worthStoring.extend(glob(path.join(iSOperationDirectory, aGlob)))
    for aFile in glob(path.join(iSOperationDirectory, "*")):
        if aFile in worthStoring:
            move(aFile, controlParameterList['eventResultDir'])


def osc2uFromOSCARFile(OSCARFilePath):
    """
        Execute osc2u program using the given path to the OSCAR file. Return the
        path to the output file.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    osc2uDirectory = path.join(controlParameterList['rootDir'], osc2uControl['mainDir'])
    osc2uOutputFilePath = path.join(osc2uDirectory, osc2uControl['outputFilename'])
    osc2uExecutable = osc2uControl['executable']

    # check executable
    checkExistenceOfExecutable(path.join(osc2uDirectory, osc2uExecutable))

    # remove output file if already exists
    if path.exists(osc2uOutputFilePath):
        remove(osc2uOutputFilePath)

    # check existence of the OSCAR file then execute
    if path.exists(OSCARFilePath):
        run("nice -n %d ./" % (ProcessNiceness) + osc2uExecutable + " < " + OSCARFilePath, cwd=osc2uDirectory)

    # save OSCAR file
    if osc2uControl['saveOSCAR']:
        move(OSCARFilePath, controlParameterList['eventResultDir'])

    # return the output file path
    return osc2uOutputFilePath


def urqmdFromOsc2uOutputFile(osc2uFilePath):
    """
        Perform urqmd using osc2u output file. Return the path to the output
        file.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    urqmdDirectory = path.join(controlParameterList['rootDir'], urqmdControl['mainDir'])
    urqmdOutputFilePath = path.join(urqmdDirectory, urqmdControl['outputFilename'])
    urqmdExecutable = urqmdControl['executable']
    urqmdExecutionEntry = urqmdControl['entryShell']

    # check executable
    checkExistenceOfExecutable(path.join(urqmdDirectory, urqmdExecutable))

    # remove output file if already exists
    if path.exists(urqmdOutputFilePath):
        remove(urqmdOutputFilePath)

    # clean up IC
    urqmdIC = path.join(urqmdDirectory, urqmdControl['ICFilename'])
    if path.exists(urqmdIC):
        remove(urqmdIC)

    # check existence of the osc2u output, move it then execute urqmd
    if path.exists(osc2uFilePath):
        move(osc2uFilePath, urqmdIC)
        run("nice -n %d bash ./" % (ProcessNiceness) + urqmdExecutionEntry, cwd=urqmdDirectory)

    # save output file
    if urqmdControl['saveOutputFile']:
        copy(urqmdOutputFilePath, controlParameterList['eventResultDir'])

    # return the output file path
    return urqmdOutputFilePath


def binUrqmdResultFiles(urqmdOutputFile):
    """
        Bin the output from URQMD to generate flows etc.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    binUDirectory = path.join(controlParameterList['rootDir'], binUtilitiesControl['mainDir'])
    binUOperationDirectory = path.join(binUDirectory, binUtilitiesControl['operationDir'])
    binUExecutable = binUtilitiesControl['executable']

    # clean up operation folder
    cleanUpFolder(binUOperationDirectory)

    # check existence urqmd output file
    if not path.exists(urqmdOutputFile):
        raise ExecutionError("URQMD output file %s not found!" % urqmdOutputFile)

    # form executable string
    executableString = "nice -n %d python ./" % (ProcessNiceness) + binUExecutable + " " + urqmdOutputFile
    # execute!
    run(executableString, cwd=binUDirectory)

    # save some of the important result files
    worthStoring = []
    for aGlob in binUtilitiesControl['saveResultGlobs']:
        worthStoring.extend(glob(path.join(binUOperationDirectory, aGlob)))
    for aFile in glob(path.join(binUOperationDirectory, "*")):
        if aFile in worthStoring:
            move(aFile, controlParameterList['eventResultDir'])

def collectEbeResultsToDatabaseFrom(folder):
    """
        Collect the mostly used results from subfolders that contain hydro
        results into a database, including ecc and flow etc.
    """
    ProcessNiceness = controlParameterList['niceness']
    # set directory strings
    collectorDirectory = path.join(controlParameterList['rootDir'], EbeCollectorControl['mainDir'])

    # for executable string
    simulationType = controlParameterList['simulation_type']
    if simulationType == 'hybrid':
        collectorExecutable = EbeCollectorControl['executable_hybrid']
        executableString = "nice -n %d python ./" % (ProcessNiceness) + collectorExecutable + " %s %g %s %s" % (folder, 1.0/(iSSParameters['number_of_repeated_sampling']*(iSSParameters["y_RB"]-iSSParameters["y_LB"])), EbeCollectorParameters['subfolderPattern'], EbeCollectorParameters['databaseFilename'])
    elif simulationType == 'hydro':
        collectorExecutable = EbeCollectorControl['executable_hydro']
        executableString = "nice -n %d python ./" % (ProcessNiceness) + collectorExecutable + " %s %s %s" %  (folder, EbeCollectorParameters['subfolderPattern'], EbeCollectorParameters['databaseFilename'])

    # execute
    run(executableString, cwd=collectorDirectory)

def formAssignmentStringFromDict(aDict):
    """
        Generate a parameter-equals-value string from the given dictionary. The
        generated string has a leading blank.
    """
    result = ""
    for aParameter in aDict.keys():
        result += " {}={}".format(aParameter, aDict[aParameter])
    return result


def cleanUpFolder(aDir):
    """ Delete all data files in the given directory. """
    if path.exists(aDir):
        try:
            run("rm -rf *", cwd=aDir, echo=False)
        except OSError:
            pass # very likely the the folder is already empty
    else:
        makedirs(aDir)


def checkExistenceOfExecutable(executableFilename):
    """ Check the existence of the executable file, and compile if not. """
    if not path.exists(executableFilename):
        # build then clean
        exec_path, exec_filename = path.split(executableFilename)
        run("make", cwd=exec_path)
        # if still cannot find the executable
        if not path.exists(executableFilename):
            raise ExecutionError("Cannot generate executable %s!" % executableFilename)

def checkExistenceOfExecutables(executableFilenames):
    """
        Check the existences of the executable files, and compile them if not.
        Will call the checkExistenceOfExecutable function.
    """
    for executableFilename in executableFilenames:
        checkExistenceOfExecutable(executableFilename)


def run(command, cwd=getcwd(), echo=True):
    """ Invoke a command from terminal and wait for it to stop. """
    if echo:
        print("-"*80)
        print("In "+cwd)
        print("Executing command: "+command)
        print("-"*80)
        stdout.flush()
    return call(command, shell=True, cwd=cwd)


def sequentialEventDriverShell():
    """
        Perform a sequential calculations for a given number of events.
        Parameters are read from dictionaries given by allParameterList.
    """
    try:
        # read parameters
        readInParameters()
        translate_centrality_cut()

        # create result folder
        resultDir = controlParameterList['resultDir']
        if path.exists(resultDir):
            rmtree(resultDir)
            makedirs(resultDir)

        # get simulation type
        simulationType = controlParameterList['simulation_type']

        # generate initial conditions then loop over initial conditions
        event_id = 0
        # print current progress to terminal
        stdout.write("PROGRESS: %d events out of %d finished.\n" % (event_id, controlParameterList['numberOfEvents']))
        stdout.flush()
        for aInitialConditionFile in generateSuperMCInitialConditions(controlParameterList['numberOfEvents']):
            # get the result folder name for storing results, then create it if necessary
            event_id += 1
            eventResultDir = path.join(resultDir, controlParameterList['eventResultDirPattern'] % event_id)
            controlParameterList['eventResultDir'] = eventResultDir
            if path.exists(eventResultDir):
                rmtree(eventResultDir)
            makedirs(eventResultDir)

            # print current progress to terminal
            print("Starting event %d..." % event_id)

            # perform hydro calculations and get a list of all the result filenames
            hydroResultFiles = [aFile for aFile in hydroWithInitialCondition(aInitialConditionFile)]

            # fork simulation type here
            if simulationType == 'hybrid':
                # perform iSS calculation and return the path to the OSCAR file
                OSCARFilePath = iSSWithHydroResultFiles(hydroResultFiles)

                # perform osc2u
                osc2uOutputFilePath = osc2uFromOSCARFile(OSCARFilePath)

                # now urqmd
                urqmdOutputFilePath = urqmdFromOsc2uOutputFile(osc2uOutputFilePath)

                # copy and concatnate final results from all hydro events into one file
                combinedUrqmdFile = path.join(controlParameterList['resultDir'], controlParameterList['combinedUrqmdFile'])
                open(combinedUrqmdFile, 'a').writelines(open(urqmdOutputFilePath).readlines())

                # bin the combined result file to get flows
                binUrqmdResultFiles(urqmdOutputFilePath)

                # delete the huge final UrQMD combined file
                remove(urqmdOutputFilePath)

            elif simulationType == 'hydro':
                # perform iS calculation and resonance decays
                iSWithResonancesWithHydroResultFiles(hydroResultFiles)

            # print current progress to terminal
            stdout.write("PROGRESS: %d events out of %d finished.\n" % (event_id, controlParameterList['numberOfEvents']))
            stdout.flush()

        # collect mostly used data into a database
        collectEbeResultsToDatabaseFrom(resultDir)

    except ExecutionError as e:
        print("Errors encountered during execution, aborting.")
        raise
    finally:
        print("Thank you for using. Zhi Qiu, 2013-02")


if __name__ == "__main__":
    sequentialEventDriverShell()
