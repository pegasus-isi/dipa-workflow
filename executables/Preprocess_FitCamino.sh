#!/bin/sh
# Om Shanti. Om Sai Ram. Madison, WI. 08/31/2016. 11:08 a.m.
# Om Shanti. Om Sai Ram. April 13, 2015. 1:23 p.m. Madison, WI.

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --dwi) dwi="$2";;
    --out) out="$2";;
    *);;
  esac; shift
done

imagebasename="${dwi%%.*}"
outbasename="${out%%.*}"

subjId=$1
sliceNum=$2

outRoot=/scratch/Nagesh/MIDUSRef
prefix1=${outRoot}/${subjId}DWIReorientedSlice${sliceNum}
prefix2=${outRoot}/${subjId}DTISlice${sliceNum}

${CAMINO_ROOT}/image2voxel -4dimage $dwi -inputdatatype short -outputdatatype float -outputfile ${imagebasename}.Bfloat
${CAMINO_ROOT}/modelfit -inputfile ${imagebasename}.Bfloat -inputdatatype float -schemefile ${outRoot}/prescribedDW.scheme -outputdatatype float -model ldt -outputfile ${imagebasename}.Bfloat
${CAMINO_ROOT}/dt2nii -inputfile ${imagebasename}.Bfloat -inputdatatype float -header $dwi -gzip -outputroot ${prefix2}_
