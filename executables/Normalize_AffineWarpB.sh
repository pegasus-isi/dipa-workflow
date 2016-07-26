#!/bin/bash -e

#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --affmean) affmean="$2";;
    --inaffimage) inaffimage="$2";;
    --outaffimage) outaffimage="$2";;
    --outaffine) outaffine="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_AffineWarpB"
  echo "Usage: "
  echo "    Normalize_AffineWarpB.sh [options] --mean <FILE> --image <FILE> --affmean <FILE> --inaffimage <FILE> --outaffimage <FILE> --outaffine <FILE>"
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

${DTITK_ROOT}/DTI-TK/bin/affine3Dtool -in ${inaffimage} -compose ${affmean} -out ${outaffimage}
${DTITK_ROOT}/DTI-TK/bin/affineSymTensor3DVolume -in ${image} -trans ${affimage} -target ${mean} -out ${outaffine}
