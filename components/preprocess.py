#!/bin/python
from Pegasus.DAX3 import *
import os
import sys
import pandas
from utility.console import Notice
from component import Component

class preprocess(Component):
    """
    Preprocess component of DIPA.
    Uses a variety of tools from FSL and DIPY to convert raw DWI-weighted images to Semi-Positive Definite files (SPD).
    If the type of eddy correction is "eddy", the matrix expects a minimum of 7 columns:
        * ID
        * DWI
        * MASK
        * BVALS
        * BVECS
        * INDEX
        * ACQPARAMS
    Any extra columns would include those being fed in for hierarchical normalization.
    If the type of eddy correction is "eddy_correct", the matrix expects a minimum of 2 columns:
        * ID
        * DWI
    """
    def __init__(self, matrix, hierarchy=["PROJECT", "ID"], name="Project", correct_type="eddy",
                               orient_check=True, fit_type="dipy", fit_method="WLS", eddy_interp="spline",
                               is_shelled=True, multishelled=True, topup=False, eddy_flm="quadratic", eddy_slm="none", eddy_fwhm=0,
                               eddy_niters=5, eddy_fep=False, eddy_resample='jac', eddy_nvoxhp=1000, eddy_ff=10.0,
                               eddy_no_sep_offs=False, eddy_dont_peas=False, transferflag=True):
        Component.__init__(self, matrix, hierarchy, name, transferflag)

        self.correct_type = correct_type
        self.fit_type = fit_type
        self.fit_method = fit_method
        self.interp = eddy_interp
        self.orient_check = orient_check
        self.shelled = is_shelled
        self.multishelled = multishelled
        if self.correct_type == "eddy":
            self.topup = topup
            if self.topup == True:
                self.warnings.append(Notice("Warning", "Using topup is not currently implemented."))
                self.topup = False
            self.topup = topup
            self.flm = eddy_flm
            self.slm = eddy_slm
            self.fwhm = eddy_fwhm
            self.niters = eddy_niters
            self.fep = eddy_fep
            self.resample = eddy_resample
            self.nvoxhp = eddy_nvoxhp
            self.ff = eddy_ff
            self.no_sep_offs = eddy_no_sep_offs
            self.dont_peas = eddy_dont_peas

        if self.fit_type == "camino":
            self.warnings.append(Notice("Warning", "Camino is not currently implemented. Defaulting to DIPY fitting"))
            self.fit_type = "dipy"
        if self.fit_type == "dipy" and self.fit_method not in ["WLS", "OLS"]:
            self.warnings.append(Notice("Warning", "Using DIPY fitting requires either 'WLS' or 'OLS' as a fitting method. Defaulting to 'WLS'."))
            self.fit_method = "WLS"

        self.transferflag = transferflag


        #Init here

    @classmethod
    def get_arg_mappings(cls):
        args = {
        "--correct_type": "CorrectType",
        "--correct_topup":"Topup",
        "--correct_eddy_flm":"EddyFLM",
        "--correct_eddy_slm":"EddySLM",
        "--correct_eddy_fwhm":"EddyFWHM",
        "--correct_eddy_niters":"EddyNiters",
        "--correct_eddy_fep":"EddyFEP",
        "--correct_eddy_interp":"EddyInterp",
        "--correct_eddy_resamp":"EddyResample",
        "--correct_eddy_nvoxhp":"EddyNvoxhp",
        "--correct_eddy_ff":"EddyFF",
        "--correct_eddy_no_sep_offs":"EddyNoSepOffs",
        "--correct_eddy_dont_peas":"EddyDontPeas",
        "--orient_check": "OrientationCheck",
        "--fit_type": "FitType",
        "--fit_method": "FitMethod",
        "--shelled": "Shelled",
        "--multishelled": "Multishelled",
        }

        return args

    def add_to_dax(self, dax, progress):
        for full_id in list(self.matrix["FULL"]):
            #Eddy Correction
            if self.correct_type == "eddy":
                eddy_job = Preprocess_Eddy(full_id, self.topup, self.flm, self.slm, self.fwhm, self.niters, self.fep, self.interp, self.resample, self.nvoxhp, self.ff, self.no_sep_offs, self.dont_peas, self.transferflag)
            else:
                eddy_job = Preprocess_EddyCorrect(full_id, self.interp, self.transferflag)
            dax.addJob(eddy_job.pegasus_job)
            self.files.update(eddy_job.files)
            progress.increment()

            #Orientation Checking
            if self.orient_check:
                orient_check_job = Preprocess_OrientationCheck(full_id, self.transferflag)
                dax.addJob(orient_check_job.pegasus_job)
                dax.depends(parent=eddy_job.pegasus_job, child=orient_check_job.pegasus_job)
                self.files.update(orient_check_job.files)
                progress.increment()

            if self.fit_type == 'dipy':
                fit_job = Preprocess_Fit_Dipy(full_id, self.multishelled, self.fit_method, self.transferflag)
            else:
                fit_job = Preprocess_Fit_Camino()
            dax.addJob(fit_job.pegasus_job)
            self.files.update(fit_job.files)
            dax.depends(parent=eddy_job.pegasus_job, child=fit_job.pegasus_job)
            progress.increment()
            #progress.add_warning(Notice("Alert",fit_job.job_id))

        return dax

class Preprocess_Eddy(object):
    "A wrapper around FSL's eddy_openmp command"
    def __init__(self, subset_id, topup, flm, slm, fwhm, niters, fep, interp, resample, nvoxhp, ff, no_sep_offs, dont_peas, transferflag):
        self.job_id = subset_id+"_Preprocess_EddyCorrection"
        self.pegasus_job = Job(name="Preprocess_Eddy", namespace="dipa", id=self.job_id)
        self.files = {}

        imageinputfile = subset_id+"_dwi.nii.gz"
        maskinputfile = subset_id+"_dwi_mask.nii.gz"
        bvecsinputfile = subset_id+"_bvecs.txt"
        bvalsinputfile = subset_id+"_bvals.txt"
        indexinputfile = subset_id+"_index.txt"
        acqparamsinputfile = subset_id+"_acqparams.txt"

        outimagefile = subset_id+"_dwi_ecc.nii.gz"
        outrotatedbvecsfile = subset_id+"_rotated_bvecs.txt"
        outparamsfile = subset_id+"_eddy_parameters.txt"
        outmovementrmsfile = subset_id+"_eddy_movement_rms.txt"
        outmovementrmsrestrictedfile = subset_id+"_eddy_restricted_movement_rms.txt"
        outpostshellalignmentparamsfile = subset_id+"_eddy_post_eddy_shell_alignment_parameters.txt"
        outoutlierreportfile = subset_id+"_eddy_outlier_report.txt"
        outoutliermapfile = subset_id+"_eddy_outlier_map.txt"
        outoutliermapstdevfile = subset_id+"_eddy_outlier_n_stdev_map.txt"
        outoutliermapsqrfile = subset_id+"_eddy_outlier_n_sqr_stdev_map.txt"

        args = [
        "--imain", imageinputfile,
        "--mask", maskinputfile,
        "--bvecs", bvecsinputfile,
        "--bvals", bvalsinputfile,
        "--index", indexinputfile,
        "--acqp", acqparamsinputfile,
        "--outcorrected",outimagefile,
        "--outrotatedbvecs", outrotatedbvecsfile,
        "--outparams", outparamsfile,
        "--outmovementrms", outmovementrmsfile,
        "--outmovementrmsrestricted", outmovementrmsrestrictedfile,
        "--outpostshellalignmentparams", outpostshellalignmentparamsfile,
        "--outoutlierreport", outoutlierreportfile,
        "--outoutliermap", outoutliermapfile,
        "--outoutliermapstdev", outoutliermapstdevfile,
        "--outoutliermapsqr", outoutliermapsqrfile,
        "--flm", flm,
        "--slm", slm,
        "--fwhm", str(fwhm),
        "--niters", str(niters),
        "--fep", str(fep),
        "--interp", interp,
        "--resamp", resample,
        "--nvoxhp", str(nvoxhp),
        "--ff", str(ff),
        "--dont_sep_offs_move", str(no_sep_offs),
        "--dont_peas", str(dont_peas)
        ]

        input_files = [imageinputfile, maskinputfile, bvecsinputfile, bvalsinputfile, indexinputfile, acqparamsinputfile]
        output_files = [outimagefile, outrotatedbvecsfile, outparamsfile, outmovementrmsfile, outmovementrmsrestrictedfile,
                        outpostshellalignmentparamsfile, outoutlierreportfile, outoutliermapfile,
                        outoutliermapstdevfile, outoutliermapsqrfile]

        self.pegasus_job.addArguments(*args)

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            #print(outputfile)
            if outputfile in [outimagefile, outrotatedbvecsfile]:
                self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=True)
            else:
                self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)


class Preprocess_EddyCorrect(object):
    "A wrapper around FSL's eddy_openmp command"
    def __init__(self, subset_id, interp, transferflag):
        self.job_id = subset_id+"_Preprocess_EddyCorrection"
        self.pegasus_job = Job(name="Preprocess_EddyCorrect", namespace="dipa", id=self.job_id)
        self.files = {}

        imageinputfile = subset_id+"_dwi.nii.gz"

        outimagefile = subset_id+"_dwi_ecc.nii.gz"
        outrotatedbvecsfile = subset_id+"_rotated_bvecs.txt"

        args = [
        "--imain", imageinputfile,
        "--out", outimagefile,
        "--outrotatedbvecs", outrotatedbvecsfile,
        "--interp", interp,
        ]

        input_files = [imageinputfile]
        output_files = [outimagefile, outrotatedbvecsfile]

        self.pegasus_job.addArguments(*args)

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class Preprocess_OrientationCheck(object):
    "A quick dipy-based tool to visualize the orientations of the data."
    def __init__(self, subset_id, transferflag):
        self.job_id = subset_id+"_Preprocess_OrientationCheck"
        self.pegasus_job = Job(name="Preprocess_OrientationCheck", namespace="dipa", id=self.job_id)
        self.files = {}

        imageinputfile = subset_id+"_dwi_ecc.nii.gz"
        bvecsinputfile = subset_id+"_bvecs.txt"
        bvalsinputfile = subset_id+"_bvals.txt"

        outsagittalimage = subset_id+"_sagittal.png"
        outcoronalimage = subset_id+"_coronal.png"
        outaxialimage = subset_id+"_axial.png"

        args = [
        "--image", imageinputfile,
        "--bvals", bvecsinputfile,
        "--bvecs", bvalsinputfile,
        "--outsagittal", outsagittalimage,
        "--outcoronal", outcoronalimage,
        "--outaxial", outaxialimage
        ]

        input_files = [imageinputfile, bvecsinputfile, bvalsinputfile]
        output_files = [outsagittalimage, outcoronalimage, outaxialimage]

        self.pegasus_job.addArguments(*args)

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=True)

class Preprocess_Fit_Dipy(object):
    "A quick dipy-based tool to fit data."
    def __init__(self, subset_id, multishelled, fitmethod, transferflag):
        self.job_id = subset_id+"_Preprocess_Fit"
        self.pegasus_job = Job(name="Preprocess_Fit_Dipy", namespace="dipa", id=self.job_id)
        self.files = {}

        imageinputfile = subset_id+"_dwi_ecc.nii.gz"
        bvecsinputfile = subset_id+"_rotated_bvecs.txt"
        bvalsinputfile = subset_id+"_bvals.txt"

        outspd = subset_id+"_spd.nii.gz"
        outdki = subset_id+"_dki.nii.gz"
        outresidual = subset_id+"_residual.nii.gz"
        outnoise = subset_id+"_noise.nii.gz"
        outsnr = subset_id+"_snr.nii.gz"
        outfa = subset_id+"_fa.nii.gz"
        outmd = subset_id+"_md.nii.gz"
        outrd = subset_id+"_rd.nii.gz"
        outad = subset_id+"_ad.nii.gz"
        outmk = subset_id+"_mk.nii.gz"
        outrk = subset_id+"_rk.nii.gz"
        outak = subset_id+"_ak.nii.gz"

        args = [
        "--image", imageinputfile,
        "--bvals", bvalsinputfile,
        "--bvecs", bvecsinputfile,
        "--out_dti", outspd,
        "--out_residual", outresidual,
        "--out_noise", outnoise,
        "--out_snr", outsnr,
        "--out_fa", outfa,
        "--out_md", outmd,
        "--out_rd", outrd,
        "--out_ad", outad,
        "--fit_method", fitmethod
        ]

        input_files = [imageinputfile, bvecsinputfile, bvalsinputfile]
        output_files = [outspd,outresidual,outnoise,outsnr,outfa,outmd,outrd,outad]

        if multishelled:
            args.extend([
            "--out_dki", outdki,
            "--out_mk", outmk,
            "--out_rk", outrk,
            "--out_ak", outak
            ])
            output_files.extend([outdki,outmk,outrk,outak])

        self.pegasus_job.addArguments(*args)

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=True)
