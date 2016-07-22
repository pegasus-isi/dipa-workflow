#!/bin/bash
#Main coding by Andrew Schoen (schoen.andrewj@gmail.com)
#With the guidance and expertise of Nagesh Adluru (nagesh.adluru@gmail.com)
#And Nate Vack (njvack@gmail.com)
#And the assitance of Michael Stoneman (stonemanm@carleton.edu)
#University of Wisconsin - Madison

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --inputlist) input_list_file="$2";;
    --finalmean) final_mean_file="$2";;
    --fafinalmean) fa_final_mean_file="${2}";;
    --isoinputlist) iso_input_list_file="$2";;
    --isofinalmean) iso_final_mean_file="${2}";;
    --isofafinalmean) iso_fa_final_mean_file="${2}";;
    --origmean) orig_file="$2";;
    --statictemplate) static="True";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_Compose"
  echo "Usage: "
  echo "    Normalize_Compose.sh [options] --inputlist <FILE> --finalmean <FILE> --fafinalmean <FILE> --isoinputlist <FILE> --isofinalmean <FILE> --isofafinalmean <FILE> [--statictemplate --origmean <FILE>]"
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

${DTIK_ROOT}/bin/TVMean -in ${input_list_file} -out ${final_mean_file}
${DTIK_ROOT}/bin/TVMean -in ${iso_input_list_file} -out ${iso_final_mean_file}
${DTIK_ROOT}/bin/TVtool -fa -in ${final_mean_file} -out ${fa_final_mean_file}
${DTIK_ROOT}/bin/TVtool -fa -in ${iso_final_mean_file} -out ${iso_fa_final_mean_file}
