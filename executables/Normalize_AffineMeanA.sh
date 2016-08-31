#!/bin/bash -e

#Defaults:

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --invlist) inv_list_file="$2";;
    --mean) mean_file="$2";;
    --invaff) inv_aff_file="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_AffineMeanA"
  echo "Usage: "
  echo "    Normalize_AffineMeanA.sh [options] --invlist <FILE> --mean <FILE> --invaff <FILE>"
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


${DTITK_ROOT}/bin/affine3DShapeAverage ${inv_list_file} ${mean_file} ${inv_aff_file} 1
