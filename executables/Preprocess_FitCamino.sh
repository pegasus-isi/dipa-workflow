#!/bin/sh
# Om Shanti. Om Sai Ram. Madison, WI. 08/31/2016. 11:08 a.m.
# Om Shanti. Om Sai Ram. April 13, 2015. 1:23 p.m. Madison, WI.

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --dwi) dwi="$2";;
    --bvecs) bvecs="$2";;
    --bvals) bvals="$2";;
    --outbas) out="$2";;
    *);;
  esac; shift
done

imagebasename="${dwi%%.*}"
outbasename="${out%%.*}"

inputDatatype=`${FSL_ROOT}/fslval ${dwi} datatype`
if [[ ${inputDatatype} == 4 ]]; then
  inputDatatypeText=short
elif [[ ${inputDatatype} == 8 ]]
  inputDatatypeText=float
elif [[ ${inputDatatype} == 16 ]]
  inputDatatypeText=double
else
  exit 1
fi

${CAMINO_ROOT}/fsl2scheme -bvalfile ${bvals} -bvecfile ${bvecs} > 
${CAMINO_ROOT}/image2voxel -4dimage $dwi -inputdatatype ${inputDatatypeText} -outputdatatype float -outputfile ${imagebasename}.Bfloat
${CAMINO_ROOT}/modelfit -inputfile ${imagebasename}.Bfloat -inputdatatype float -schemefile ${outRoot}/prescribedDW.scheme -outputdatatype float -model nldt_pos -outputfile ${imagebasename}.Bfloat
${CAMINO_ROOT}/dt2nii -inputfile ${imagebasename}.Bfloat -inputdatatype float -header $dwi -gzip -outputroot ${prefix2}_

# nldt_pos, ldt, wls lookup fit.py

## Todo explicit output names. Lookinto Preprocess_Eddy.sh