#!/bin/python
import matplotlib.pyplot as plt
import os, sys, pandas, math, numpy
import nibabel as nib
import dipy.reconst.dti as dti
import vtk
from dipy.viz import fvtk
from dipy.segment.mask import median_otsu
from dipy.align.reslice import reslice
from dipy.core.gradients import gradient_table
from dipy.io import read_bvals_bvecs
from docopt import docopt
import dipy.data as dpd
reload(dti)
#print(vtk.vtkVersion.GetVTKMajorVersion())
import matplotlib.pyplot as plt
from xvfbwrapper import Xvfb

Version = "0.1"

doc = """
Orientation Check, Version {0}.

Usage:
    orientationcheck.py [options] --image <FILE> --bvals <FILE> --bvecs <FILE> --outsagittal <FILE> --outcoronal <FILE> --outaxial <FILE>

Options:
    -h --help               Show this screen.
    -v --version            Show version.
    --image <FILE>          Image File (path).
    --bvals <FILE>          BVALS File (path).
    --bvecs <FILE>          BVECS File (path).
    --outsagittal <FILE>    Output File (path).
    --outaxial <FILE>       Output File (path).
    --outcoronal <FILE>     Output File (path).
""".format(Version)

#============================================================================
#             General Utility
#============================================================================

def cleanPathString(path):
  if path.endswith("/"):
    path = path[:-1]
  if path.startswith("="):
    path = path[1:]
  realpath = os.path.realpath(path)
  return realpath


def exists(path):
    #Shorthand for checking the existence of a file
    if os.path.exists(cleanPathString(path)):
        return(1)
    else:
        print("Error: Input file '{0}' not found!".format(path))
        return(0)

def run(rawargs):
    arguments = docopt(doc, argv=rawargs, version='Orientation Check v{0}'.format(Version))
    inputs = [{"Value":"image file", "Flag": "--image"}, {"Value":"bvec file", "Flag": "--bvecs"}, {"Value":"bvec file", "Flag": "--bvecs"}]
    for inputinfo in inputs:
        if not exists(arguments[inputinfo["Flag"]]):
            print("The {0} specified does not exist!".format(inputinfo["Value"]))
            sys.exit(1)

    try:
        rawimage = nib.load(arguments["--image"])
        bvals, bvecs = read_bvals_bvecs(arguments['--bvals'], arguments['--bvecs'])
        #print(bvals)
        #print(bvecs)
        print("Generating gradient table.")
        gtab = gradient_table(bvals, bvecs)

        #Define the tensor model
        print("Generating the tensor model.")
        dti_wls = dti.TensorModel(gtab, fit_method="NLLS")

        image_data = rawimage.get_data()


        print("Masking the brain.")
        image_masked, mask = median_otsu(image_data, 3, 1, autocrop=True, dilate=2)
        #print(image_masked)
        #image_masked_data = nib.nifti1.Nifti1Image(image_masked.astype(np.float32), image_data.get_affine())
        #print("Saving masked brain image")
        #nib.nifti1.save(image_masked_data, "./imagemasked.nii.gz")
        print("Resampling the brain to a standard resolution.")
        image, affine1 = reslice(image_masked, rawimage.get_affine(), rawimage.get_header().get_zooms()[:3], (3.0,3.0,3.0))
        mask, maskaffine1 = reslice(mask.astype(numpy.int), rawimage.get_affine(), rawimage.get_header().get_zooms()[:3], (3.0,3.0,3.0))
        #print(len([type(mask) for i in range(0,image.shape[3])]))
        #mask = numpy.expand_dims(mask,3)
        #print(mask)
        #print(mask.shape)
        #image=image*mask
        print(image[0][0][0])

        print("Checking the image dimensions")
        Xsize, Ysize, Zsize, directions = image.shape
        print("X: {0}\nY: {1}\nZ: {2}".format(Xsize, Ysize, Zsize))

        #Define Image Scopes
        print("Defining the image scopes.")
        imagedict = {"axial": {"dropdim": [0,1], "scope": (slice(0,Xsize), slice(0,Ysize), slice(math.floor(Zsize/2),math.floor(Zsize/2)+1))},
                     "coronal": {"dropdim": [0,2], "scope": (slice(0,Xsize), slice(math.floor(Ysize/2),math.floor(Ysize/2)+1), slice(0, Zsize))},
                     "sagittal": {"dropdim": [1,2], "scope": (slice(math.floor(Xsize/2),math.floor(Xsize/2)+1), slice(0,Ysize), slice(0, Zsize))}}


        #roi_idx = (slice(0,image.shape[0]), slice(0,image.shape[1]), slice(middleslice,middleslice+1))#(slice(0,image.shape[0]), slice(0,image.shape[1]), slice(int(image.shape[2]/2),int(image.shape[2]/2)+1))
        print("Defining sphere.")
        #sphere = dpd.get_sphere('symmetric724')
        sphere = dpd.get_sphere('symmetric362')

        #Slice the whole dataset by the scope
        print("Slicing the dataset with the scopes.")
        for view in ["sagittal", "coronal", "axial"]:
            imagedict[view]["image"] = image[imagedict[view]["scope"]]
            imagedict[view]["mask"] = mask[imagedict[view]["scope"]]
            print("Fitting {0} data.".format(view))
            fit_wls = dti_wls.fit(imagedict[view]["image"])
            print("Extracting {0} FA.".format(view))
            fa1 = fit_wls.fa * imagedict[view]["mask"]
            print("Extracting {0} EVALS.".format(view))
            evals1 = fit_wls.evals
            print("Extracting {0} EVECS.".format(view))
            evecs1 = fit_wls.evecs
            print("Extracting {0} Color FA.".format(view))
            cfa1 = dti.color_fa(fa1, evecs1)
            cfa1 = cfa1/cfa1.max()
            print("Defining {0} renderer.".format(view))
            render = fvtk.ren()
            print("Generating {0} image.".format(view))
            x =cfa1.shape[imagedict[view]["dropdim"][0]]
            y =cfa1.shape[imagedict[view]["dropdim"][1]]

            #print(x, y, 1, 3)
            cfa2 = cfa1.reshape(x, y, 1, 3)
            evals2 = evals1.reshape(x, y, 1, 3)*1.25
            evecs2 = evecs1.reshape(x, y, 1, 3, 3)*1.25
            print("Adding render.")
            fvtk.add(render, fvtk.tensor(evals2, evecs2, cfa2, sphere))
            print("Recording render.")
            with Xvfb() as xvfb:
                fvtk.record(render, out_path=arguments["--out"+view], size=(800,800), magnification=2)
            print("Image Saved")

    except:
        print("Could not check orientation of output image.")
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    args = sys.argv
    del args[0]
    run(args)
