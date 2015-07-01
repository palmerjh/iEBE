from sys import argv, exit
from os import path
import math

rap_range = (-2.5, 2.5)

folder = path.abspath(argv[1])

# check input file
UrQMDoutputFilePath = path.join(folder, "urqmdCombined.txt")
if not path.isfile(UrQMDoutputFilePath):
    exit("Cannot find UrQMD output file: " + UrQMDoutputFilePath)

# open output file
outFile = path.join(folder, "extractedData.dat")
open(outFile, "w").write("")

pTList = []
etaList = []
phiList = []
pidList = []

# convert UrQMD outputs and fill them into file
# that will be read to make TTree objects for flow analysis
read_mode = "header_first_part"
header_count = 1 # the first read line is already part of the header line
data_row_count = 0
nParticles = 0 # not the same as data_row_count; excludes particles not in rap_range

eventID = 0
for aLine in open(UrQMDoutputFilePath):
    if read_mode=="header_first_part":
        if header_count <= 14: # skip first 14 lines
            header_count += 1
            continue
        # now at 15th line
        assert header_count==15, "No no no... Stop here."
        try:
            data_row_count = int(aLine.split()[0])
        except ValueError as e:
            print("The file "+ UrQMDoutputFilePath +" does not have a valid urqmd output file header!")
            exit(e)
        read_mode = "header_second_part"
    elif read_mode=="header_second_part":
        # skip current line by switching to data reading mode
        read_mode = "data_part"
    elif read_mode=="data_part":
        if data_row_count>0:
            # still have data to read
            try:
                p0, px, py, pz = map(lambda x: float(x), aLine[65:128].split())
                pid = int(aLine[151:157])
                rap = 0.5*math.log((p0 + pz)/(p0 - pz))
                if rap < rap_range[1] and rap > rap_range[0]:
                    pT = math.sqrt(px*px + py*py)
                    pMag = math.sqrt(pT*pT + pz*pz)
                    phi = math.atan2(py, px)
                    pseudorap = 0.5*math.log((pMag + pz)/(pMag - pz))

                    pTList.append(pT)
                    etaList.append(pseudorap)
                    phiList.append(phi)
                    pidList.append(pid)

                    nParticles += 1

            except ValueError as e:
                print("The file "+ UrQMDoutputFilePath +" does not have valid urqmd data!")
                exit(e)
            data_row_count -= 1
        if data_row_count == 1: # note: not 0, but 1
            assert len(pTList) == nParticles, "Oops"
            with open(outFile, "a") as f:
                f.write(str(nParticles) + '\n')
        
                for x in range(nParticles):
                    f.write(str(pTList.pop()) + ' ')
                f.write('\n')
                
                for x in range(nParticles):
                    f.write(str(etaList.pop()) + ' ')
                f.write('\n')
                
                for x in range(nParticles):
                    f.write(str(phiList.pop()) + ' ')
                f.write('\n')
                
                for x in range(nParticles):
                    f.write(str(pidList.pop()) + ' ')
                f.write('\n')

            eventID += 1
            print("processing UrQMD event %d finished." % eventID)

            # switch back to header mode
            data_row_count = 0
            nParticles = 0
            header_count = 0 # not pointing at the header line yet
            read_mode = "header_first_part"