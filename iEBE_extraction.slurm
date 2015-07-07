#!/usr/bin/env bash
#SBATCH --ntasks=1
#SBATCH --time=0-00:10:00
#SBATCH --array=1-10

JOB=$SLURM_ARRAY_TASK_ID

(python ./utilities/readUrQMD.py /store/user/tuos/hydroiEBE/test/RESULTS/job-${JOB} &> /store/user/tuos/hydroiEBE/test/RESULTS/job-${JOB}/readUrQMD.log)

cp ./utilities/makeTree.C /home/palmerjh/CMSSW_7_5_0_pre5/src
cd /home/palmerjh/CMSSW_7_5_0_pre5/src

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc472
eval `scramv1 runtime -sh`

FILE=/store/user/tuos/hydroiEBE/test/RESULTS/job-${JOB}/extractedData.dat
root -q -b 'makeTree.C("'$FILE'", $JOB)' &> tree_creation_${JOB}.log

exit 0

