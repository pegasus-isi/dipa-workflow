#!/usr/bin/env python
import os, sys, pandas, math
import numpy as np
import nibabel as nib
import dipy.reconst.dki as dki
import dipy.reconst.dti as dti
from dipy.segment.mask import median_otsu
from dipy.align.reslice import reslice
from dipy.core.gradients import gradient_table
from dipy.io import read_bvals_bvecs
from docopt import docopt

Version = "0.1"

doc = """
Fit, Version {0}.

Usage:
    fit.py [options] --image <FILE> --bvals <FILE> --bvecs <FILE>

Options:
    -h --help                   Show this screen.
    -v --version                Show version.
    --image <FILE>              Input image file (path).
    --mask <FILE>               Mask image in same coordinate space as image, optional. (path) [default: None]
    --bvals <FILE>              BVALS file (path).
    --bvecs <FILE>              BVECS file (path).
    --out_dti <FILE>            Output the 6 diffusion tensor parameters of the dti data (path). [default: None]
    --out_dki <FILE>            Output the 15 kurtosis tensor parameters of the dki data (path). [default: None]
    --out_residual <FILE>       Output the residual of the model fitting (path). [default: None]
    --out_noise <FILE>          Output the standard deviation across directions of the residual (path). [default: None]
    --out_snr <FILE>            Output the average B0 over noise file (path). [default: None]
    --out_fa <FILE>             Output the FA from the dti model (path). [default: None]
    --out_md <FILE>             Output the MD from the dti model (path). [default: None]
    --out_rd <FILE>             Output the RD from the dti model (path). [default: None]
    --out_ad <FILE>             Output the AD from the dti model (path). [default: None]
    --out_mk <FILE>             Output the MK from the dki model (path). [default: None]
    --out_rk <FILE>             Output the RK from the dki model (path). [default: None]
    --out_ak <FILE>             Output the AK from the dki model (path). [default: None]
    --fit_method <METHOD>       Specify a method for fitting (WLS or OLS). [default: WLS]
    --mask_median_radius <INT>  Radius (in voxels) of the applied median filter [default: 4]
    --mask_numpass <INT>        Number of pass of the median filter [default: 4]

""".format(Version)

#============================================================================
#             Classes
#============================================================================

class Fitter(object):
    def __init__(self, data, mask, gradient_table, fit_method, median_radius=4, numpass=4, out_dti=None, out_dki=None, out_residual=None, out_noise=None, out_snr=None, out_fa=None, out_md=None, out_rd=None, out_ad=None, out_mk=None, out_rk=None, out_ak=None):
        self.raw_data = data
        self.mask = mask
        self.data = self.raw_data
        self.gradient_table = gradient_table
        self.median_radius = int(median_radius)
        self.numpass = int(numpass)

        #Generate an average B0 image
        values = np.array(self.gradient_table.bvals)
        if len(np.unique(values)) > 2:
            self.multishelled = True
        else:
            self.multishelled = False
        ii = np.where(values == self.gradient_table.bvals.min())[0]
        self.b0_average = np.mean(self.data.get_data()[:,:,:,ii], axis=3)

        #Fitted
        #self.dti_fitted = None
        self.fitted = None


        #Raw-Type values
        self.out_dti = None
        if self.multishelled:
            self.out_dti_path = out_dti
        else:
            self.out_dti_path = None
        self.out_dki = None
        self.out_dki_path = out_dki
        self.out_residual = None
        self.out_residual_path = out_residual
        self.out_noise = None
        self.out_noise_path = out_noise
        self.out_snr = None
        self.out_snr_path = out_snr

        self.fit_method = fit_method

        #Outcome Measures
        self.out_fa = None
        self.out_fa_path = out_fa
        self.out_md = None
        self.out_md_path = out_md
        self.out_rd = None
        self.out_rd_path = out_rd
        self.out_ad = None
        self.out_ad_path = out_ad
        if self.multishelled:
            self.out_mk_path = out_mk
            self.out_rk_path = out_rk
            self.out_ak_path = out_ak
        else:
            self.out_mk_path = None
            self.out_rk_path = None
            self.out_ak_path = None
        self.out_mk = None
        self.out_rk = None
        self.out_ak = None


    def save(self):
        out_matrix = [
        [self.out_dti_path, self.out_dti],
        [self.out_dki_path, self.out_dki],
        [self.out_residual_path, self.out_residual],
        [self.out_noise_path, self.out_noise],
        [self.out_snr_path, self.out_snr],
        [self.out_fa_path, self.out_fa],
        [self.out_md_path, self.out_md],
        [self.out_rd_path, self.out_rd],
        [self.out_ad_path, self.out_ad],
        [self.out_mk_path, self.out_mk],
        [self.out_rk_path, self.out_rk],
        [self.out_ak_path, self.out_ak],
        ]
        for path, contents in out_matrix:
            if path != None and contents != None:
                if path.endswith(".nii.gz"):
                    pass
                elif path.endswith(".nii"):
                    path += ".gz"
                else:
                    path += ".nii.gz"
                print("Saving {0}".format(path))
                nib.nifti1.save(contents, path)

    def apply_mask(self):
        """
        If self.mask is not None, will mask the raw_data with the mask provided.
        If self.mask is None, median_otsu is used to generate those files.
        """
        if self.mask == None:
            print("Generating mask with median_otsu.")
            raw_data = self.raw_data.get_data()
            masked_data, mask = median_otsu(raw_data, self.median_radius, self.numpass)

            #Update the instance
            self.data = nib.nifti1.Nifti1Image(masked_data.astype(np.float32), self.raw_data.get_affine())
            self.mask = nib.nifti1.Nifti1Image(mask.astype(np.int_), self.data.get_affine())
        else:
            print("Masking data with provided mask.")
            raw_data = self.raw_data.get_data()
            mask_data = self.mask.get_data()
            masked_data = raw_data * mask_data

            #Update the instance
            self.data = nib.nifti1.Nifti1Image(masked_data.astype(np.float32), self.raw_data.get_affine())

        #Regenerate an average B0 image
        values = np.array(self.gradient_table.bvals)
        ii = np.where(values == self.gradient_table.bvals.min())[0]
        self.b0_average = np.mean(self.data.get_data()[:,:,:,ii], axis=3)

    def fit(self):
        """
        Fits a dki model to the data
            Standard DTI measures (FA,MD,RD,AD) are calculated from the DKI model, accounting for additional variance.
            DKI measures of MK,RK,AK are computed from the DKI model.
            Residual image has the same dimensions as the original input image. Calculated as |Avg(B0_volumes)-predicted_image|
            Noise is equal to the stdev across volumes of the residual image, and SNR is Avg(B0_volumes)/Noise, removing NaNs.
        """
        data = self.data.get_data()

        #Generate the dk model
        print("Generating the models.")
        if self.multishelled:
            model = dki.DiffusionKurtosisModel(self.gradient_table, fit_method=self.fit_method)
        else:
            model = dti.TensorModel(self.gradient_table, fit_method=self.fit_method)

        print("Fitting the data.")
        self.fitted = model.fit(data)

        #Generate the lower-triangular dataset
        if self.multishelled:
            print("Generating the kurtosis tensor data.")
            self.out_dti = nib.nifti1.Nifti1Image(self.fitted.lower_triangular(), self.data.get_affine())
            self.out_dki = nib.nifti1.Nifti1Image(self.fitted.kt, self.data.get_affine())
        else:
            print("Generating the tensor data.")
            self.out_dti = nib.nifti1.Nifti1Image(self.fitted.lower_triangular(), self.data.get_affine())
            self.out_dki = None

        #Generate the residuals
        if self.out_residual_path != None or self.out_noise_path != None or self.out_snr_path != None:
            print("Estimating input data.")
            estimate_data = self.fitted.predict(self.gradient_table, S0=self.b0_average)
            print("Calculating residuals.")
            residuals = np.absolute(data - estimate_data)
            noise = np.std(residuals, axis=3)
            snr = np.nan_to_num(self.b0_average / noise)
            self.out_residual = nib.nifti1.Nifti1Image(residuals.astype(np.float32), self.data.get_affine())
            self.out_noise = nib.nifti1.Nifti1Image(noise.astype(np.float32), self.data.get_affine())
            self.out_snr = nib.nifti1.Nifti1Image(snr.astype(np.float32), self.data.get_affine())


    def extract_scalars(self):
        self.out_fa = nib.nifti1.Nifti1Image(self.fitted.fa.astype(np.float32), self.data.get_affine())
        self.out_md = nib.nifti1.Nifti1Image(self.fitted.md.astype(np.float32), self.data.get_affine())
        self.out_rd = nib.nifti1.Nifti1Image(self.fitted.rd.astype(np.float32), self.data.get_affine())
        self.out_ad = nib.nifti1.Nifti1Image(self.fitted.ad.astype(np.float32), self.data.get_affine())
        if self.multishelled:
            self.out_mk = nib.nifti1.Nifti1Image(self.fitted.mk().astype(np.float32), self.data.get_affine())
            self.out_rk = nib.nifti1.Nifti1Image(self.fitted.rk().astype(np.float32), self.data.get_affine())
            self.out_ak = nib.nifti1.Nifti1Image(self.fitted.ak().astype(np.float32), self.data.get_affine())

#============================================================================
#             Run
#============================================================================

def run(rawargs):
    arguments = docopt(doc, argv=rawargs, version='Fit v{0}'.format(Version))

    configuration = {}

    #Try to load the image data. If successful, save it to configuration as "data"
    try:
        configuration["data"] = nib.load(arguments["--image"])
    except:
        print("The image you specified does not exist, or cannot be read.")
        sys.exit(1)

    #Try to load the mask data. If successful, save it to configuration as "mask"
    if arguments["--mask"] != None and arguments["--mask"] != "None":
        try:
            configuration["mask"] = nib.load(arguments["--mask"])
        except:
            print("The mask image you specified does not exist, or cannot be read.")
            sys.exit(1)
    else:
        configuration["mask"] = None

    #Try to load the bvec, bvals files. If successful, save it to configuration as "gradient_table"
    try:
        bvals, bvecs = read_bvals_bvecs(arguments["--bvals"], arguments["--bvecs"])
        configuration["gradient_table"] = gradient_table(bvals, bvecs)
    except:
        print("Could not read bvec and/or bval file")
        sys.exit(1)

    #Update configuration with more basic settings
    lookup = {"--out_dti": "out_dti",
              "--out_dki": "out_dki",
              "--out_residual": "out_residual",
              "--out_noise": "out_noise",
              "--out_snr": "out_snr",
              "--out_fa": "out_fa",
              "--out_md": "out_md",
              "--out_rd": "out_rd",
              "--out_ad": "out_ad",
              "--out_mk": "out_mk",
              "--out_rk": "out_rk",
              "--out_ak": "out_ak",
              "--mask_median_radius": "median_radius",
              "--mask_numpass": "numpass"}

    for key, value in lookup.iteritems():
        if arguments[key] == "None" or arguments[key] == None:
            configuration[value] = None
        else:
            configuration[value] = arguments[key]


    if arguments["--fit_method"].upper() in ["WLS", "OLS"]:
        configuration["fit_method"] = arguments["--fit_method"].upper()
    else:
        print("'{0}' is not a valid fit method. Choose either 'WLS', 'OLS'".format(arguments["--fit_method"].upper()))
        sys.exit(1)

    fitter = Fitter(**configuration)
    fitter.apply_mask()
    fitter.fit()

    fitter.extract_scalars()
    fitter.save()
    sys.exit(0)

#============================================================================
#             Main
#============================================================================

if __name__ == '__main__':
   args = sys.argv
   del args[0]
   run(args)
