#!/bin/bash


#Main coding by Andrew Schoen (schoen.andrewj@gmail.com)
#With the guidance and expertise of Nagesh Adluru (nagesh.adluru@gmail.com)
#And Nate Vack (njvack@gmail.com)
#And the assitance of Michael Stoneman (stonemanm@carleton.edu)
#University of Wisconsin - Madison
errcount=0
PROJECT=$1

#/study3/reference/pegasus-dev/sandbox/dipa_test/Monitor/statusupdate.py ${PROJECT} CreateTemplate Running
#echo "DIPA Step: Create Template for ${PROJECT}"
#cd /study3/reference/pegasus-dev/sandbox/dipa_test/Data/Project/Normalize

if [ x${DTIK_ROOT} == x ] ; then
    echo "DTIK_ROOT is not set "
    errcount=$((errcount + 1))
fi


if [ x${EXECUTABLE_DIR} == x ] ; then
    echo "EXECUTABLE_DIR is not set "
    errcount=$((errcount + 1))
fi

if . ${DTIK_ROOT}/scripts/dtitk_common.sh ; then
  errcount=$((errcount + 0))
else
  echo 'There was an error with Source, line' $(( $LINENO - 3 ))
  errcount=$((errcount + 1))
fi


echo "System PATH is set to ${PATH}"

# no need for this. Karan
# set in the transformation catalog
#if export DTITK_ROOT=/home/schoen/Public/DIPA/ThirdParty/DTI-TK ; then
#  errcount=$((errcount + 0))
#else
#  echo 'There was an error with Export Root, line' $(( $LINENO - 3 ))
#  errcount=$((errcount + 1))
#fi

if ${EXECUTABLE_DIR}/settemplatedim.py --inputfile=./image_dimension_files.csv --outputprefix=./template ; then
  errcount=$((errcount + 0))
else
  echo 'There was an error with settemplatedim, line' $(( $LINENO - 3 ))
  errcount=$((errcount + 1))
fi


if ${DTIK_ROOT}/bin/TVMean -in ./initial_template_input.txt -out ./initial_template_orig.nii.gz ; then
  errcount=$((errcount + 0))
else
  echo 'There was an error with TVMean, line' $(( $LINENO - 3 ))
  errcount=$((errcount + 1))
fi


resample=`cat ./template_resample_bool.txt`
if [[ $resample == True ]] ; then
    if ${DTIK_ROOT}/bin/TVResample -in ./initial_template_orig.nii.gz -vsize `cat ./template_vsize.txt` -size `cat ./template_dim.txt` -out ./initial_template.nii.gz ; then
	errcount=$((errcount + 0))
    else
	echo 'There was an error with TVResample, line' $(( $LINENO - 3 ))
	errcount=$((errcount + 1))
    fi
else
    cp ./initial_template_orig.nii.gz ./initial_template.nii.gz ;
 fi

if cp ./initial_template.nii.gz ./mean_rigid0.nii.gz ; then
  errcount=$((errcount + 0))
else
  echo 'There was an error with Copy, line' $(( $LINENO - 3 ))
  errcount=$((errcount + 1))
fi



if [[ $errcount == 0 ]] ; then
#    /study3/reference/pegasus-dev/sandbox/dipa_test/Monitor/statusupdate.py ${PROJECT} CreateTemplate Finished
    echo "DIPA Step: Create Template for ${PROJECT} --> COMPLETE!"
    exit 0
else
    /study3/reference/pegasus-dev/sandbox/dipa_test/Monitor/statusupdate.py ${PROJECT} CreateTemplate Error
    echo "DIPA Step: Create Template for ${PROJECT} --> ERROR!"
    exit 1
fi
