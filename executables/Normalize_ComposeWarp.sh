#!/bin/bash -e

#Defaults:

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --image) image="$2";;
    --mean) mean="$2";;
    --aff) aff_file="$2";;
    --df) df_file="$2";;
    --isovsize) isovsizefile="$2";;
    --warped) warped="$2";;
    --isowarped) isowarped="$2";;
    --warp) warp="$2";;
    --invwarp) invwarp="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_ComposeWarp"
  echo "Usage: "
  echo "    Normalize_ComposeWarp.sh [options] --image <FILE> --mean <FILE> --aff <FILE> --df <FILE> --isovsize <FILE> --warped <FILE> --isowarped <FILE> --warp <FILE> --invwarp <FILE>"
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

aff_inv="${aff_file%%.*}"_inv.aff
df_inv="${df_file%%.*}"_inv.df.nii.gz

${DTITK_ROOT}/bin/dfRightComposeAffine -aff ${aff_file} -df ${df_file} -out ${warp}
${DTITK_ROOT}/bin/affine3Dtool -in ${aff_file} -invert -out ${aff_inv}
${DTITK_ROOT}/bin/dfToInverse -in ${df_file} -out ${df_inv}
${DTITK_ROOT}/bin/dfLeftComposeAffine -df ${df_inv} -aff ${aff_inv} -out ${invwarp}

${DTITK_ROOT}/bin/deformationSymTensor3DVolume -in ${image} -out ${warped} -trans ${warp} -target ${mean}
${DTITK_ROOT}/bin/deformationSymTensor3DVolume -in ${image} -out ${isowarped} -trans ${warp} -target ${mean} -vsize `cat ${isovsizefile}`
