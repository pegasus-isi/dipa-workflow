#!/bin/bash -e

#Main coding by Andrew Schoen (schoen.andrewj@gmail.com)
#With the guidance and expertise of Nagesh Adluru (nagesh.adluru@gmail.com)
#And Nate Vack (njvack@gmail.com)
#And the assitance of Michael Stoneman (stonemanm@carleton.edu)
#University of Wisconsin - Madison
#Defaults:
smoption="NMI"
initial="False"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --mean) mean="$2";;
    --image) image="$2";;
    --smoption) smoption="$2";;
    --sepcoarse) sepcoarse="$2";;
    --initial) initial="True"
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_DiffeomorphicMean"
  echo "Usage: "
  echo "    Normalize_DiffeomorphicMean.sh [options] --diffeolist <FILE> --dflist <FILE> --newmean <FILE> --dfmean <FILE> [--statictemplate --previousmean <FILE>]"
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
else:
  bool=""

#First iteration
${DTITK_ROOT}/scripts/dti_rigid_reg ${mean} ${image} ${smoption} ${sepcoarse} ${sepcoarse} ${sepcoarse} 0.01 ${bool}
