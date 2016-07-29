#!/bin/bash -e

#Defaults
smoption="NMI"
initial="False"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --outimage) outimage="$2";;
    --outaff) outaff="$2";;
    --smoption) smoption="$2";;
    --sepcoarse) sepcoarse="$2";;
    --initial) initial="True";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_RigidWarp"
  echo "Usage: "
  echo "    Normalize_RigidWarp.sh [options] --mean <FILE> --image <FILE> --outimage <FILE> --outaff <FILE> --smoption <STR> --sepcoarse <STR> [--initial]"
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

if [ $initial == "True" ] ; then
  bool="1"
else
  bool=""
fi

${DTITK_ROOT}/scripts/dti_rigid_reg ${mean} ${image} ${smoption} ${sepcoarse} ${sepcoarse} ${sepcoarse} 0.01 ${bool}

#Output the files, named correctly.
imagebasename="${image%%.*}"
mv ${imagebasename}_aff.nii.gz ${outimage}
mv ${imagebasename}.aff ${outaff}
