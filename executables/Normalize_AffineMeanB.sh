#!/bin/bash -e

#Defaults:
static="False"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --affinelist) affine_list_file="$2";;
    --mean) mean_file="$2";;
    --trace) tr_file="$2";;
    --mask) mask_file="$2";;
    --staticmean) static="True";;
    *);;
  esac; shift
done

if [[ "${show_help}" == "True" ]] ; then
  echo "Normalize_AffineMeanB"
  echo "Usage: "
  echo "    Normalize_AffineMeanB.sh [options] --affinelist <FILE> --mean <FILE> --trace <FILE> --mask <FILE> [--staticmean]"
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

if [[ ${static} == "False" ]] ; then

  ${DTITK_ROOT}/bin/TVMean -in ${affine_list_file} -out ${mean_file}

fi

${DTITK_ROOT}/bin/TVtool -tr -in ${mean_file} -out ${tr_file}

${DTITK_ROOT}/bin/BinaryThresholdImageFilter ${tr_file} ${mask_file} 0 .01 100 1 0
