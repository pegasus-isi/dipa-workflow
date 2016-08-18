#!/bin/bash -e

#Defaults
smoption="NMI"
initial="False"
aff="None"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --aff) aff="$2";;
    --outimage) outimage="$2";;
    --outaff) outaff="$2";;
    --smoption) smoption="$2";;
    --sep) sep="$2";;
    --initial) initial="True";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_RigidWarp"
  echo "Usage: "
  echo "    Normalize_RigidWarp.sh [options] --mean <FILE> --image <FILE> --outimage <FILE> --outaff <FILE> --smoption <STR> --sep <STR> [--initial 1]"
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

imagebasename="${image%%.*}"

if [ $initial == "True" ] ; then
  endcode=""
else
  endcode="1"
  ln -s $aff ${imagebasename}.aff
fi
echo ${DTITK_ROOT}/scripts/dti_rigid_reg ${mean} ${image} ${smoption} ${sep} ${sep} ${sep} 0.01 ${endcode}
${DTITK_ROOT}/scripts/dti_rigid_reg ${mean} ${image} ${smoption} ${sep} ${sep} ${sep} 0.01 ${endcode}

#Output the files, named correctly.

mv ${imagebasename}_aff.nii.gz ${outimage}
mv ${imagebasename}.aff ${outaff}
