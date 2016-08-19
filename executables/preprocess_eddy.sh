#!/bin/bash -e

topup="NONE"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --type) eddytype="$2";;               #EDDY/EDDY_CORRECT
    --imain) imain="$2";;                 #EDDY/EDDY_CORRECT
    --mask) mask="$2";;                   #EDDY
    --index) index="$2";;                 #EDDY
    --acqp) acqp="$2";;                   #EDDY
    --bvecs) bvecs="$2";;                 #EDDY
    --bvals) bvals="$2";;                 #EDDY
    --out) out="$2";;                     #EDDY/EDDY_CORRECT
    --topup) topup="$2";;                 #EDDY
    --flm) flm="$2";;                     #EDDY
    --slm) slm="$2";;                     #EDDY
    --fwhm) fwhm="$2";;                   #EDDY
    --niter) niter="$2";;                 #EDDY
    --fep) fep="$2";;                     #EDDY
    --interp) interp="$2";;               #EDDY/EDDY_CORRECT
    --resamp) resamp="$2";;               #EDDY
    --nvoxhp) nvoxhm="$2";;               #EDDY
    --ff) ff="$2";;                       #EDDY
    --no_sepoffs_mv) no_sepoffs_mv="$2";; #EDDY
    --dont_peas) dont_peas="$2";;         #EDDY
    *);;
  esac; shift
done


if [[ $eddytype == "eddy" ]] ; then
  #Perform eddy processing
  inputstring=" "
  if [[ ${imain}x != x ]] ; then
    inputstring="$inputstring --imain $imain"
  else:
    echo "No main image specified!"
    exit 1
  fi
  if [[ ${mask}x != x ]] ; then
    inputstring="$inputstring --mask $mask"
  else:
    echo "No mask image specified!"
    exit 1
  fi
  if [[ ${index}x != x ]] ; then
    inputstring="$inputstring --index $index"
  else:
    echo "No index file specified!"
    exit 1
  fi
  if [[ ${acqp}x != x ]] ; then
    inputstring="$inputstring --acqp $acqp"
  else:
    echo "No acqp file specified!"
    exit 1
  fi
  if [[ ${bvecs}x != x ]] ; then
    inputstring="$inputstring --bvecs $bvecs"
  else:
    echo "No bvecs file specified!"
    exit 1
  fi
  if [[ ${bvals}x != x ]] ; then
    inputstring="$inputstring --bvals $bvals"
  else:
    echo "No bvals file specified!"
    exit 1
  fi
  if [[ ${out}x != x ]] ; then
    inputstring="$inputstring --out $out"
  else:
    echo "No out file specified!"
    exit 1
  fi
  if [[ ${topup} != "NONE" ]] ; then
    inputstring="$inputstring --topup $topup"
  fi
  if [[ ${flm}x != x ]] ; then
    inputstring="$inputstring --flm $flm"
  fi
  if [[ ${slm}x != x ]] ; then
    inputstring="$inputstring --slm $slm"
  fi
  if [[ ${fwhm}x != x ]] ; then
    inputstring="$inputstring --fwhm $fwhm"
  fi
  if [[ ${niter}x != x ]] ; then
    inputstring="$inputstring --niter $niter"
  fi
  if [[ ${fep}x != x ]] ; then
    inputstring="$inputstring --fep $fep"
  fi
  if [[ ${interp}x != x ]] ; then
    inputstring="$inputstring --interp $interp"
  fi
  if [[ ${resamp}x != x ]] ; then
    inputstring="$inputstring --resamp $resamp"
  fi
  if [[ ${nvoxhp}x != x ]] ; then
    inputstring="$inputstring --nvoxhp $nvoxhp"
  fi
  if [[ ${ff}x != x ]] ; then
    inputstring="$inputstring --ff $ff"
  fi
  if [[ ${no_sepoffs_mv}x != x ]] ; then
    inputstring="$inputstring --dont_sep_offs_move"
  fi
  if [[ ${dont_peas}x != x ]] ; then
    inputstring="$inputstring --dont_peas"
  fi

  ${FSL_ROOT}/eddy_openmp $inputstring

else
  #Perform eddy_correct processing
  if [[ ${imain}x != x ]] ; then
    inputstring="$inputstring --imain $imain"
  else:
    echo "No main image specified!"
    exit 1
  fi
  if [[ ${out}x != x ]] ; then
    inputstring="$inputstring --out $out"
  else:
    echo "No out file specified!"
    exit 1
  fi
  ${FSL_ROOT}/eddy_correct ${imain} ${out} 0 $interp
fi
