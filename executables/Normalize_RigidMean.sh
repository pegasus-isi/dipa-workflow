#!/bin/bash -e

#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --affinelist) affine_list_file="$2";;
    --newmean) new_mean_file="$2";;
    --previousmean) previous_mean_file="$2";;
    --smoption) smoption="${2}";;
    --statictemplate) static="True";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_RigidMean"
  echo "Usage: "
  echo "    Normalize_RigidMean.sh [options] --affinelist <FILE> --newmean <FILE> --previousmean <FILE> --smoption <OPTION> --similarityfile <FILE> [--statictemplate]"
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
  ${DTITK_ROOT}/bin/TVMean -in ${affine_list_file} -out ${new_mean_file}
fi
