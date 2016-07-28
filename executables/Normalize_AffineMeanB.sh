#!/bin/bash

#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --affinelist) affine_list_file="$2";;
    --mean) mean_file="$2";;
    --trace) tr_file="$2";;
    --mask) mask_file="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_AffineMeanB"
  echo "Usage: "
  echo "    Normalize_AffineMeanB.sh [options] --affinelist <FILE> --newmean <FILE> --newtrace <FILE> --newmask <FILE> --previousmean <FILE> [--statictemplate]"
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

${DTIK_ROOT}/bin/TVMean -in ${affine_list_file} -out ${mean_file}

${DTIK_ROOT}/bin/TVtool -tr -in ${mean_file} -out ${tr_file}

${DTIK_ROOT}/bin/BinaryThresholdImageFilter ${tr_file} ${mask_file} 0 .01 100 1 0
