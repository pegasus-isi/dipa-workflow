#!/bin/bash -e

#Defaults
static="False"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --inputlist) input_list_file="$2";;                   #Normalization
    --finalmean) final_mean_file="$2";;                   #Normalization/Registration
    --fafinalmean) fa_final_mean_file="${2}";;            #Normalization/Registration
    --isoinputlist) iso_input_list_file="$2";;            #Normalization
    --isofinalmean) iso_final_mean_file="${2}";;          #Normalization/Registration
    --isofafinalmean) iso_fa_final_mean_file="${2}";;     #Normalization/Registration
    --origmean) orig_file="$2";;                          #Registration
    --isovsizefile) iso_vsize_file="$2";;                 #Registration
    --dimsizefile) dim_file="$2";;                        #Registration
    --statictemplate) static="True";;                     #Registration
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

if [[ $static == "True" ]] ; then
  cp ${orig_file} ${final_mean_file}
  ${DTITK_ROOT}/bin/TVResample -in ${final_mean_file} -vsize `cat ${iso_vsize_file}` -size `cat ${dim_file}` -out ${iso_final_mean_file}
else
  ${DTITK_ROOT}/bin/TVMean -in ${input_list_file} -out ${final_mean_file}
  ${DTITK_ROOT}/bin/TVMean -in ${iso_input_list_file} -out ${iso_final_mean_file}
fi

${DTITK_ROOT}/bin/TVtool -fa -in ${final_mean_file} -out ${fa_final_mean_file}
${DTITK_ROOT}/bin/TVtool -fa -in ${iso_final_mean_file} -out ${iso_fa_final_mean_file}
