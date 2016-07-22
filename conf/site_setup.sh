#!/bin/bash

#Use this file to set custom settings, such as the path to FSL, DTI-TK, etc.
#DTI-TK
export DTITK_ROOT=`readlink -f ../../Public/bin/dtitk`

#FSL
export FSL_ROOT=`which fsl`
