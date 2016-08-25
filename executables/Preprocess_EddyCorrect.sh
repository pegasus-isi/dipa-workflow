#!/bin/bash -e

#Defaults
interp='spline'

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --imain) imain="$2";;
    --out) out="$2";;
    --outrotatedbvecs) outbvecs="$2";;
    --interp) interp="$2";;
    *);;
  esac; shift
done

#Environmental variable checking
if [ x${FSL_ROOT} == x ] ; then
    echo "FSL_ROOT is not set "
fi


if [ x${EXECUTABLE_DIR} == x ] ; then
    echo "EXECUTABLE_DIR is not set "
fi


#Perform eddy_correct processing
if [[ ${imain}x == x ]] ; then
  echo "No main image specified!"
  exit 1
fi
if [[ ${out}x == x ]] ; then
  echo "No out file specified!"
  exit 1
fi
${FSL_ROOT}/eddy_correct ${imain} ${out} 0 $interp
