#!/bin/bash -e

#Defaults:
smoption="NMI"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --mask) mask="$2";;
    --iterations) iterations="$2";;
    --outimage) outimage="$2";;
    --outdf) outdf="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_DiffeomorphicWarp"
  echo "Usage: "
  echo "    Normalize_DiffeomorphicWarp.sh [options] --mean <FILE> --image <FILE> --iterations <INT> --outimage <FILE> --outdf <FILE>"
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

${DTITK_ROOT}/scripts/dti_diffeomorphic_reg ${mean} ${image} ${mask} 1 ${iterations} 0.002

#Output the files, named correctly.
imagebasename="${image%%.*}"
mv ${imagebasename}_diffeo.nii.gz ${outimage}
mv ${imagebasename}_diffeo.df.nii.gz ${outdf}
