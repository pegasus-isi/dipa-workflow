#!/bin/bash

topup="NONE"

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --type) eddytype="$2";;               #EDDY/EDDY_CORRECT
    --imain) imain="$2";;                 #EDDY/EDDY_CORRECT
    --mask) mask="$2";;                   #EDDY
    --index) index="$2";;                 #EDDY
    --acqp) acqparams="$2";;              #EDDY
    --bvecs) bvecs="$2";;                 #EDDY
    --bvals) bvals="$2";;                 #EDDY
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

else
  #Perform eddy_correct processing

fi
