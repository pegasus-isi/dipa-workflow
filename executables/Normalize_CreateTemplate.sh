#!/bin/bash -e

#Defaults:
resample_bool_file="./template_resample_bool.txt"
vsize_file="./template_vsize.txt"
iso_vsize_file="./template_iso_vsize.txt"
dim_file="./template_dim.txt"
existing_template_file="None"  #"None" being a dummy value replaced with a filename if it exists.

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --lookupfile) lookup_file="$2";;
    --templateinputsfile) template_inputs_file="$2";;
    --resamplefile) resample_bool_file="$2";;
    --vsizefile) vsize_file="$2";;
    --isovsizefile) iso_vsize_file="$2";;
    --dimsizefile) dim_file="$2";;
    --orig) orig_template_file="$2";;
    --initial) initial_template_file="$2";;
    --srctemplate) existing_template_file="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_CreateTemplate"
  echo "Usage: "
  echo "    Normalize_CreateTemplate.sh [options] --lookupfile <FILE> --templateinputsfile <FILE> [--resamplefile <FILE> --vsizefile <FILE> --isovsizefile <FILE>] --dimsizefile <FILE> --orig <FILE> --initial <FILE> --rigid <FILE>"
  echo "    Normalize_CreateTemplate.sh [options] --lookupfile <FILE> --template <FILE>  [--resamplefile <FILE> --vsizefile <FILE> --isovsizefile <FILE>] --dimsizefile <FILE> --orig <FILE> --initial <FILE> --rigid <FILE>"
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


${EXECUTABLE_DIR}/settemplatedim.py --inputfile ${lookup_file} --out_dim ${dim_file} --out_vsize ${vsize_file} --out_iso_vsize ${iso_vsize_file} --out_resample_bool ${resample_bool_file}

resample=`cat ${resample_bool_file}`

if [[ "${existing_template_file}" == "None" ]] ; then

  ${DTITK_ROOT}/bin/TVMean -in ${template_inputs_file} -out ${orig_template_file}

else

  orig_template_file="${existing_template_file}"

fi

if [[ $resample == "True" ]] ; then
  ${DTITK_ROOT}/bin/TVResample -in ${orig_template_file} -vsize `cat ${vsize_file}` -size `cat ${dim_file}` -out ${initial_template_file}
else
  cp ${orig_template_file} ${initial_template_file}
fi
