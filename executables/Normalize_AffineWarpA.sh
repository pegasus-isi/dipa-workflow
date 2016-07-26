#!/bin/bash -e

#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --smoption) smoption="$2";;
    --sepcoarse) sepcoarse="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_AffineWarp"
  echo "Usage: "
  echo "    Normalize_AffineWarp.sh [options] --mean <FILE> --image <FILE> --smoption <STR> --sepcoarse <STR>"
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


${DTITK_ROOT}/scripts/dti_affine_reg ${mean} ${image} ${smoption} ${sepcoarse} ${sepcoarse} ${sepcoarse} 0.01 1
