#!/usr/bin/env python

"""
    This module specializes binUtilities to process data produced mainly by the iSS code.
"""

import numpy
from os import makedirs, path
from shutil import copy
from fileRVer2 import readNumericalData
from listR import FLL
from dataStreamTransformer import strStream2BlockStream
import assignmentFormat
import binUtilities

# "global" parameters
pTBin_table_filename = "bin_tables/pT_bins.dat" # for differential
pTAll_table_filename = "bin_tables/pT_bins_2.5.dat" # for integrated

particle_count_pT_range_filename = "bin_tables/particle_count_pT_range.dat" # used to count particles lie in this range

pT_has_name = "pT"
phi_has_name = "phi"
pid_has_name = "PID"

calculate_flow_from_order = 1
calculate_flow_to_order = 9

differential_flow_saveTo = "results/differential_flow_%s.dat"
differential_flow_format_saveTo = "results/differential_flow_format.dat"

integrated_flow_saveTo = "results/integrated_flow_%s.dat"
integrated_flow_format_saveTo = "results/integrated_flow_format.dat"

count_particle_number_in_pT_range = "results/event_number_of_particles_in_pT_range.dat"

if not path.exists("results"): makedirs("results")
copy(pTBin_table_filename, "results")
copy(pTAll_table_filename, "results")

#-----------------------------------------------------------------------------------
# define reusable bins
pTBin = binUtilities.SingleVarBin(FLL(strStream2BlockStream(open(pTBin_table_filename))),  pT_has_name) # for differential
pTAll = binUtilities.SingleVarBin(FLL(strStream2BlockStream(open(pTAll_table_filename))),  pT_has_name) # for integrated

# define reuable actions
returnPT = binUtilities.SingleVarValue(pT_has_name) # generate mean pT

particle_count_pT_range = readNumericalData(particle_count_pT_range_filename)
countNumberInPTRangeAction = binUtilities.CountInRange(pT_has_name, particle_count_pT_range[0][0], particle_count_pT_range[1][0])

class CalculateFlow(binUtilities.ActionObject):
    """ This class calculate the flow.
    """
    def __init__(self, fromOrder=1, toOrder=9, phi_name="phi", pT_name="pT"):
        self.phi_name = phi_name # useful only when phi is renamed
        self.pT_name = pT_name
        self.orderList = numpy.array(range(fromOrder, toOrder+1))
        self.cplxOrderList = numpy.array(range(fromOrder, toOrder+1))*1j
        self.storeResult = numpy.zeros(len(self.orderList)+1)+1j*numpy.zeros(len(self.orderList)+1)

    def action(self, sample, sampleFormat): # same interface
        """ Calculate flows: <exp(i*order*phi)> for order in between
            self.fromOrder and self.toOrder.
        """
        self.storeResult[1:] = numpy.exp(self.cplxOrderList*sample[int(sampleFormat[self.phi_name])])
        self.storeResult[0] = sample[sampleFormat[self.pT_name]]
        return self.storeResult

    def getDataFormatStrings(self):
        """
            Return a list of strings describing flows.
        """
        strings = ["pT"]
        strings.extend("v_%d" % order for order in self.orderList)
        return strings

flowAction = CalculateFlow(calculate_flow_from_order, calculate_flow_to_order, phi_name=phi_has_name, pT_name=pT_has_name)

#------------------------------------------------------------------------------------
# combine bin and action to processes
differentialFlowCharged = binUtilities.BinProcess(pTBin, flowAction)
differentialFlowCharged.saveTo = differential_flow_saveTo % "total"
differentialFlowCharged.saveFormatTo = differential_flow_format_saveTo
differentialFlowCharged.useCplx = True

integratedFlowCharged = binUtilities.BinProcess(pTAll, flowAction)
integratedFlowCharged.saveTo = integrated_flow_saveTo % "total"
integratedFlowCharged.saveFormatTo = integrated_flow_format_saveTo
integratedFlowCharged.useCplx = True


def generateFlowActionsForPids(Pid_table):
    """
        Generate BinProcess objects for all particles given in the Pid_table
        list. The list should contain elements of type (particle_name,
        pid_value). The "particle_name" will be fed into the %s for
        differential_flow_saveTo and integrated_flow_saveTo strings.
    """
    binProcess = []
    for particle_name, pid in Pid_table:
        # differential flow
        tmpProcess = binUtilities.BinProcess(
            binUtilities.SingleVarBinCheckingField(FLL(strStream2BlockStream(open(pTBin_table_filename))), pT_has_name, pid, pid_has_name),
            flowAction
        )
        tmpProcess.saveTo = differential_flow_saveTo % particle_name
        tmpProcess.saveFormatTo = differential_flow_format_saveTo
        tmpProcess.useCplx = True
        binProcess.append(tmpProcess)
        # integrated flow
        tmpProcess = binUtilities.BinProcess(
            binUtilities.SingleVarBinCheckingField(FLL(strStream2BlockStream(open(pTAll_table_filename))), pT_has_name, pid, pid_has_name),
            flowAction
        )
        tmpProcess.saveTo = integrated_flow_saveTo % particle_name
        tmpProcess.saveFormatTo = integrated_flow_format_saveTo
        tmpProcess.useCplx = True
        binProcess.append(tmpProcess)
    return binProcess


# fillin the to-use binProcess list
useBinProcesses = []
# extend the list before calling the function below, like:
#if use_bin_processes["calculate differential flow"]: useBinProcesses.extend([differentialFlow])
#if use_bin_processes["calculate integrated flow"]: useBinProcesses.extend([integratedFlow])
#if use_bin_processes["count particles in pT range"]: useBinProcesses.extend([countParticleNumberInPTRange])


#-------------------------------------------------------------------------------------
# Main function used to bin data
def binISSDataFile(data_filename, format_filename, data_block_size_filename=None):
    """
        This function is a shell that perform all the defined binning process to a
        data file generated by iSS program. Here data_filename gives the main data
        file, format_filename gives the format of the data file (see formatter), and
        data_block_size_filename is the control file that is used to devide data
        into blocks.
    """
    # generate block-related non-reusable bin processes
    if data_block_size_filename:
        # define blockBin objects (they are not re-usable: each binProcess should use a different blockBin object)
#        blockSizes = [float(aLine) for aLine in file(data_block_size_filename)]
        blockSizes = numpy.loadtxt(data_block_size_filename)
        generateBlocks = binUtilities.BlockBin(blockSizes)
        # define particle counting bin process (within certain pT range specified in particle_count_pT_range_filename)
        countParticleNumberInPTRange = binUtilities.BinProcess(generateBlocks, countNumberInPTRangeAction)
        countParticleNumberInPTRange.saveTo = count_particle_number_in_pT_range

    # get data format
    raw_format = assignmentFormat.assignmentExprStream2IndexDict(open(format_filename))

    # call binDataStream function to finish the binning
    binUtilities.binDataStream(open(data_filename), raw_format, useBinProcesses)


# Main function used to bin data
def binISSDataFileSimple(data_filename, format_filename, useBinProcesses):
    """
        Simpler version of binISSDataFile
    """
    # get data format
    raw_format = assignmentFormat.assignmentExprStream2IndexDict(open(format_filename))

    # call binDataStream function to finish the binning
    binUtilities.binDataStream(open(data_filename), raw_format, useBinProcesses)
