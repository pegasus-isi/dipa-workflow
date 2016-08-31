#!/bin/bash -e

topup="NONE"
dont_peas="False"
flm="quadratic"
slm="none"
fwhm="0"
niter="5"
fep="False"
interp="spline"
resamp='jac'
nvoxhp="1000"
ff="10.0"
no_sepoffs_mv="False"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --imain) imain="$2";;
    --mask) mask="$2";;
    --index) index="$2";;
    --acqp) acqp="$2";;
    --bvecs) bvecs="$2";;
    --bvals) bvals="$2";;
    --outcorrected) outcorrected="$2";;
    --outrotatedbvecs) outbvecs="$2";;
    --outparams) outparams="$2";;
    --outmovementrms) outmovementrms="$2";;
    --outpostshellalignmentparams) outpostshellalignmentparams="$2";;
    --outoutlierreport) outoutlierreport="$2";;
    --outoutliermap) outoutliermap="$2";;
    --outoutliermapstdev) outoutliermapstdev="$2";;
    --outoutliermapsqr) outoutliermapsqr="$2";;
    --topup) topup="$2";;
    --flm) flm="$2";;
    --slm) slm="$2";;
    --fwhm) fwhm="$2";;
    --niter) niter="$2";;
    --fep) fep="$2";;
    --interp) interp="$2";;
    --resamp) resamp="$2";;
    --nvoxhp) nvoxhm="$2";;
    --ff) ff="$2";;
    --no_sepoffs_mv) no_sepoffs_mv="$2";;
    --dont_peas) dont_peas="$2";;
    *);;
  esac; shift
done

#Environmental variable checking
if [ x${FSL_ROOT} == x ] ; then
  echo "FSL_ROOT is not set "
else
  echo FSL_ROOT: ${FSL_ROOT}
fi


if [ x${EXECUTABLE_DIR} == x ] ; then
    echo "EXECUTABLE_DIR is not set "
fi

inputstring=""
if [[ ${imain}x != x ]] ; then
  inputstring="$inputstring --imain=$imain --out=${imain%%.*}_out"
else
  echo "No main image specified!"
  exit 1
fi
if [[ ${mask}x != x ]] ; then
  inputstring="$inputstring --mask=$mask"
else
  echo "No mask image specified!"
  exit 1
fi
if [[ ${index}x != x ]] ; then
  inputstring="$inputstring --index=$index"
else
  echo "No index file specified!"
  exit 1
fi
if [[ ${acqp}x != x ]] ; then
  inputstring="$inputstring --acqp=$acqp"
else
  echo "No acqp file specified!"
  exit 1
fi
if [[ ${bvecs}x != x ]] ; then
  inputstring="$inputstring --bvecs=$bvecs"
else
  echo "No bvecs file specified!"
  exit 1
fi
if [[ ${bvals}x != x ]] ; then
  inputstring="$inputstring --bvals=$bvals"
else
  echo "No bvals file specified!"
  exit 1
fi
if [[ ${topup} != "NONE" ]] ; then
  inputstring="$inputstring --topup=$topup"
fi

if [[ ${flm} != "quadratic" ]] ; then
  inputstring="$inputstring --flm=${flm}"
fi
if [[ ${slm} != "none" ]] ; then
  inputstring="$inputstring --slm=${slm}"
fi
if [[ ${fwhm} != "0" ]] ; then
  inputstring="$inputstring --fwhm=${fwhm}"
fi
if [[ ${niter} != "5" ]] ; then
  inputstring="$inputstring --niters=${niter}"
fi
if [[ ${interp} != "spline" ]] ; then
  inputstring="$inputstring --interp=${interp}"
fi
if [[ ${resamp} != "jac" ]] ; then
  inputstring="$inputstring --resamp=${resamp}"
fi
if [[ ${nvoxhp} != "1000" ]] ; then
  inputstring="$inputstring --nvoxhp=${nvoxhp}"
fi
if [[ ${ff} != "10.0" ]] ; then
  inputstring="$inputstring --ff=${ff}"
fi
if [[ ${no_sepoffs_mv} != "False" ]] ; then
  inputstring="$inputstring --dont_sep_offs_move"
fi
if [[ ${fep} != "False" ]] ; then
  inputstring="$inputstring --fep"
fi
if [[ ${dont_peas} != "False" ]] ; then
  inputstring="$inputstring --dont_peas"
fi

for val in Input:${imain} Input:${mask} Input:${index} Input:${acqp} Input:${bvals} Input:${bvecs} ; do
  if [[ $val == "Input:" ]] ; then
    echo "One or more in file was not specified! Exiting."
    exit 1
  else
    echo $val
  fi
done

for val in Output:${outcorrected} Output:${outbvecs} Output:${outparams} Output:${outmovementrms} Output:${outpostshellalignmentparams} Output:${outoutlierreport} Output:${outoutliermap} Output:${outoutliermapstdev} Output:${outoutliermapsqr} ; do
  if [[ $val == "Output:" ]] ; then
    echo "One or more out file was not specified! Exiting."
    exit 1
  else
    echo $val
  fi
done

echo ${FSL_ROOT}/eddy_openmp $inputstring --data_is_shelled --verbose
${FSL_ROOT}/eddy_openmp $inputstring --data_is_shelled
ls ${imain%%.*}_out.*
mv ${imain%%.*}_out.nii.gz $outcorrected
mv ${imain%%.*}_out.eddy_rotated_bvecs $outbvecs
mv ${imain%%.*}_out.eddy_parameters $outparams
mv ${imain%%.*}_out.eddy_movement_rms $outmovementrms
mv ${imain%%.*}_out.eddy_post_eddy_shell_alignment_parameters $outpostshellalignmentparams
mv ${imain%%.*}_out.eddy_outlier_report $outoutlierreport
mv ${imain%%.*}_out.eddy_outlier_map $outoutliermap
mv ${imain%%.*}_out.eddy_outlier_n_stdev_map $outoutliermapstdev
mv ${imain%%.*}_out.eddy_outlier_n_sqr_stdev_map $outoutliermapsqr
