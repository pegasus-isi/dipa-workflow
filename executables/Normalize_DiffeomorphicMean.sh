#!/bin/bash

#Main coding by Andrew Schoen (schoen.andrewj@gmail.com)
#With the guidance and expertise of Nagesh Adluru (nagesh.adluru@gmail.com)
#And Nate Vack (njvack@gmail.com)
#And the assitance of Michael Stoneman (stonemanm@carleton.edu)
#University of Wisconsin - Madison
#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --diffeolist) diffeo_list_file="$2";;
    --dflist) df_list_file="$2";;
    --newmean) new_mean_file="$2";;
    --dfmean) new_dfmean_file="$2";;
    --previousmean) previous_mean_file="$2";;
    --statictemplate) static="True";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_DiffeomorphicMean"
  echo "Usage: "
  echo "    Normalize_DiffeomorphicMean.sh [options] --diffeolist <FILE> --dflist <FILE> --newmean <FILE> --dfmean <FILE> [--statictemplate --previousmean <FILE>]"
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

if [[ $static == "True" ]] ; then
  cp ${previous_mean_file} ${new_mean_file}
else
  ${DTIK_ROOT}/bin/TVMean -in ${diffeo_list_file} -out ${new_mean_file}
fi

${DTIK_ROOT}/bin/VVMean -in ${df_list_file} -out ${new_dfmean_file}


${DTIK_ROOT}/bin/dfToInverse -in ${new_dfmean_file} -out ${mean_df_inv}


${DTIK_ROOT}/bin/deformationSymTensor3DVolume -in ${new_mean_file} -out ${new_mean_file} -trans ${mean_df_inv}
