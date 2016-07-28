#!/bin/bash -e

#Defaults:

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --invmean) invmean="$2";;
    --inaff) inaff="$2";;
    --outaff) outaff="$2";;
    --outaffimage) outaffimage="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_AffineWarpB"
  echo "Usage: "
  echo "    Normalize_AffineWarpB.sh [options] --mean <FILE> --image <FILE> --invmean <FILE> --inaff <FILE> --outaff <FILE> --outaffimage <FILE>"
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

${DTITK_ROOT}/DTI-TK/bin/affine3Dtool -in ${inaff} -compose ${invmean} -out ${outaff}

${DTITK_ROOT}/DTI-TK/bin/affineSymTensor3DVolume -in ${image} -trans ${outaff} -target ${mean} -out ${outaffimage}
