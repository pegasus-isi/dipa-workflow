#!/bin/bash -e

#Main coding by Andrew Schoen (schoen.andrewj@gmail.com)
#With the guidance and expertise of Nagesh Adluru (nagesh.adluru@gmail.com)
#And Nate Vack (njvack@gmail.com)
#And the assitance of Michael Stoneman (stonemanm@carleton.edu)
#University of Wisconsin - Madison

while [[ "$#" > 1 ]]; do case $1 in
    --dimfile) image_dimension_file="$2";;
    --resamplefile) resample_bool_file="$2";;
    --vsizefile) vsizefile_file="$2";;
    --dimsizefile) sizefile_file="$2";;
    --orig) orig_template_file="$2";;
    --initial) initial_template_file="$2";;
    *);;
  esac; shift
done
#PROJECT=$1


#Environmental variable checking
if [ x${DTITK_ROOT} == x ] ; then
    echo "DTITK_ROOT is not set "
fi


if [ x${EXECUTABLE_DIR} == x ] ; then
    echo "EXECUTABLE_DIR is not set "
fi

echo "System PATH is set to ${PATH}"

#Source dtitk_common.sh
source ${DTITK_ROOT}/scripts/dtitk_common.sh



${EXECUTABLE_DIR}/settemplatedim.py --inputfile=./image_dimension_files.csv --outputprefix=./template


${DTITK_ROOT}/bin/TVMean -in ./initial_template_input.txt -out ./initial_template_orig.nii.gz


resample=`cat ./template_resample_bool.txt`
if [[ $resample == True ]] ; then
  ${DTITK_ROOT}/bin/TVResample -in ./initial_template_orig.nii.gz -vsize `cat ./template_vsize.txt` -size `cat ./template_dim.txt` -out ./initial_template.nii.gz
else
  cp ./initial_template_orig.nii.gz ./initial_template.nii.gz
fi

cp ./initial_template.nii.gz ./mean_rigid0.nii.gz
