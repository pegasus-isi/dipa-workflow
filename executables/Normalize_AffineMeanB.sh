#!/bin/bash

#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --affinelist) affine_list_file="$2";;
    --newmean) new_mean_file="$2";;
    --newtrace) new_tr_file="$2";;
    --newmask) new_mask_file="$2";;
    --previousmean) previous_mean_file="$2";;
    --statictemplate) static="True";;
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

if [[ $static == "True" ]] ; then
  cp ${previous_mean_file} ${new_mean_file}
else
  ${DTIK_ROOT}/bin/TVMean -in ${affine_list_file} -out ${new_mean_file}
fi

${DTIK_ROOT}/bin/TVtool -tr -in ${new_mean_file} -out ${new_tr_file}

${DTIK_ROOT}/bin/BinaryThresholdImageFilter ${new_tr_file} ${new_mask_file} 0 .01 100 1 0
