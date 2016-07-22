#!/bin/bash


#Main coding by Andrew Schoen (schoen.andrewj@gmail.com)
#With the guidance and expertise of Nagesh Adluru (nagesh.adluru@gmail.com)
#And Nate Vack (njvack@gmail.com)
#And the assitance of Michael Stoneman (stonemanm@carleton.edu)
#University of Wisconsin - Madison
#Defaults:

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --invlist) inv_list_file="$2";;
    --invmean) inv_mean_file="$2";;
    --invaff) inv_aff_file="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_AffineMeanA"
  echo "Usage: "
  echo "    Normalize_AffineMeanA.sh [options] --invlist) <FILE> --invmean <FILE> --invaff <FILE>"
  exit 0
fi

#Environmental variable checking
if [ x${DTITK_ROOT} == x ] ; then
    echo "DTITK_ROOT is not set "
fi


if [ x${EXECUTABLE_DIR} == x ] ; then
    echo "EXECUTABLE_DIR is not set "
fi

#Source dtitk_common.sh
source ${DTITK_ROOT}/scripts/dtitk_common.sh


${DTIK_ROOT}/bin/affine3DShapeAverage ${inv_list_file} ${inv_mean_file} ${inv_aff_file} 1
