#!/bin/bash -e

#Defaults:
composed_files=""
invcomposed_files=""

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --image) image="$2";;
    --mean) mean="$2";;
    --isovsize) isovsizefile="$2";;
    --composed) composed_files="${composed_files} ${2}";;
    --invcomposed) invcomposed_files="${invcomposed_files} ${2}";;
    --outcomposed) out_composedfile="$2";;
    --outinvcomposed) out_invcomposedfile="$2";;
    --outwarped) out_warped="$2";;
    --outisowarped) out_isowarped="$2";;
    *);;
  esac; shift
done

if [[ $show_help == "True" ]] ; then
  echo "Normalize_CreateFullComposedWarp"
  echo "Usage: "
  echo "    Normalize_CreateFullComposedWarp.sh [options] --image <FILE> --mean <FILE> --aff <FILE> --df <FILE> --isovsize <FILE> --warped <FILE> --isowarped <FILE> --warp <FILE> --invwarp <FILE>"
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


#Forward
starting=""
for composed_file in $composed_files ; do
  if [[ x${starting} != x ]] ; then
    echo dfComposition -df1 $starting -df2 $composed_file -out ${out_composedfile}
    dfComposition -df1 $starting -df2 $composed_file -out ${out_composedfile}
    starting="${out_composedfile}"
  else
    starting=$composed_file
  fi
done
#Backward
starting=""
for invcomposed_file in $invcomposed_files ; do
  if [[ x${starting} != x ]] ; then
    dfComposition -df1 $starting -df2 $invcomposed_file -out ${out_invcomposedfile}
    starting="${out_invcomposedfile}"
  else
    starting=$invcomposed_file
  fi
done
${DTITK_ROOT}/bin/deformationSymTensor3DVolume -in ${image} -out ${out_warped} -trans ${out_composedfile} -target ${mean}
${DTITK_ROOT}/bin/deformationSymTensor3DVolume -in ${image} -out ${out_isowarped} -trans ${out_composedfile} -target ${mean} -vsize `cat ${isovsizefile}`
