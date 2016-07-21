#!/bin/bash
#$ -S /bin/bash
#============================================================================
#
#  Program:     DTI ToolKit (DTI-TK)
#  Module:      $RCSfile: dtitk_common.sh,v $
#  Language:    bash
#  Date:        $Date: 2011/12/21 20:39:22 $
#  Version:     $Revision: 1.1.1.1 $
#
#  Copyright (c) Gary Hui Zhang (garyhuizhang@gmail.com).
#  All rights reserverd.
#
#  DTI-TK is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  DTI-TK is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with DTI-TK.  If not, see <http://www.gnu.org/licenses/>.
#============================================================================

# define path
export PATH=${DTITK_ROOT}/bin:${DTITK_ROOT}/scripts:${DTITK_ROOT}/utilities:${PATH}

# no core dump
ulimit -c 0

#
# utility: compute TV suffix
#

function getTVPrefix {
if [ $# -lt 1 ]
then
	echo "Usage: $0 filename"
	exit 1
fi
for suf in nii nii.gz hdr img img.gz vtk aff pwa hpwa
do
	pref=${1%.$suf}
	if [ $1 != $pref ]
	then
		echo $pref
		return 0
	fi
done
return 1
}

#
# utility: check exit code
#

function check_exit_code {
if [ $# -lt 1 ]
then
	echo "Usage: $0 exit code"
	exit 1
fi
if [ $1 -ne 0 ]
then
	echo "Terminating due to error"
	exit 1
fi
}

# DTITK_USE_QSUB flag
if [ -z "${DTITK_USE_QSUB}" ]
then
	export DTITK_USE_QSUB=0
fi

if [ "${DTITK_USE_QSUB}" -eq 1 ]
then
	echo "running on host: `hostname`"
	echo "command: $0 $*"
	echo
fi

# DTITK_RIGID_FINE flag
if [ -z "${DTITK_RIGID_FINE}" ]
then
	export DTITK_RIGID_FINE=0
fi

# DTITK_AFFINE_FINE flag
if [ -z "${DTITK_AFFINE_FINE}" ]
then
	export DTITK_AFFINE_FINE=0
fi

#
#  customized qsub
#
dtitk_qsub="qsub ${DTITK_QSUB_QUEUE}"

## the multi-iteration starting levels for deformable registration
## the first element is just buffer, not used!
start=( 0  2     3     3     4     4     5     )

## use one of the two sets of parameters by commenting out 
## the set that you do not want to use
## you can also create and use your set

## the parameters tuned for deformable registration
## between a pair of human brains (stronger regularization)
## the first element is just buffer, not used!
## reg=(   0  0.080 0.072 0.064 0.056 0.048 0.040 )
## prior=( 0  0.200 0.180 0.160 0.140 0.120 0.100 )

## the parameters tuned for building human brain population-based template
## and for registering a human brain to a population-based template
## (weaker regularization)
## the first element is just buffer, not used!
reg=(   0  0.040 0.036 0.032 0.028 0.024 0.020 )
prior=( 0  0.100 0.090 0.080 0.070 0.060 0.050 )

## extreme jacobian values allowed
## strong constraint
## jaclimit=(0.04 25)
## moderate constraint
jaclimit=(0.02 50) # February 27, 2015. 10:04 a.m. Madison, WI. Back to the defaults.
# Om Shanti. Om Sai Ram. February 19, 2015. 12:37 p.m. Madison, WI.
# jaclimit=(0 50)
## weak constraint
## jaclimit=(0.01 100)

## length scale in mm
if [ -z "${DTITK_SPECIES}" ]
then
	export DTITK_SPECIES="HUMAN"
fi

if [ ${DTITK_SPECIES} == "HUMAN" ]
then
	## for human brain
	lengthscale=1.0
elif [ ${DTITK_SPECIES} == "MONKEY" ]
then
	## for monkey
	lengthscale=0.5
elif [ ${DTITK_SPECIES} == "RAT" ]
then
	## for rat
	lengthscale=0.1
fi

