#!/bin/bash -e

#Defaults:

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --diffeolist) diffeo_list_file="$2";;
    --dflist) df_list_file="$2";;
    --mean) mean_file="$2";;
    --dfmean) dfmean_file="$2";;
    --invdfmean) inv_dfmean_file="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_DiffeomorphicMean"
  echo "Usage: "
  echo "    Normalize_DiffeomorphicMean.sh [options] --diffeolist <FILE> --dflist <FILE> --mean <FILE> --dfmean <FILE> --invdfmean <FILE>"
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

${DTITK_ROOT}/bin/TVMean -in ${diffeo_list_file} -out ${mean_file}
${DTITK_ROOT}/bin/VVMean -in ${df_list_file} -out ${dfmean_file}
${DTITK_ROOT}/bin/dfToInverse -in ${dfmean_file} -out ${inv_dfmean_file}
${DTITK_ROOT}/bin/deformationSymTensor3DVolume -in ${mean_file} -out ${mean_file} -trans ${inv_dfmean_file}
