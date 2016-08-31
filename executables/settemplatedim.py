#!/usr/bin/env python


import os, sys, pandas, math
from docopt import docopt

Version = "0.1"

doc = """
Set Template Dimensions, Version {0}.

Usage:
    settemplatedim.py [options] --inputfile <FILE> [--out_dim <FILE>] [--out_vsize <FILE>] [--out_iso_vsize <FILE>] [--out_resample_bool <FILE>]

Options:
    -h --help                     Show this screen.
    -v --version                  Show version.
    --inputfile <FILE>            Input File (path).
    --out_dim <FILE>              Output path to the file which contains information about the number of voxels in the image. [default: ./template_dim.txt]
    --out_vsize <FILE>            Output path to the file which contains information about the size of voxels in the image. [default: ./template_vsize.txt]
    --out_iso_vsize <FILE>        Output path to the file which contains information about the size of voxels in the isometric image. [default: ./template_iso_vsize.txt]
    --out_resample_bool <FILE>    Output path to the file which contains information about the whether resampling is necessary. [default: ./template_resample_bool.txt]
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

def thresholdedVal(x, thresh):
    if x > thresh:
        returnval = thresh
    else:
        returnval = x
    return returnval

def hasRepeat(inputlist):
    checked = []
    for i in inputlist:
        if i in checked:
            return True
        else:
            checked.append(i)
    return False

def exists(path):
    #Shorthand for checking the existence of a file
    if os.path.exists(cleanPathString(path)):
        return(1)
    else:
        print("Error: Input file '{0}' not found!".format(path))
        return(0)

def writeToFile(text, filename):
  #Write to a file
  try:
      with open(filename, 'w+') as filebuffer:
          filebuffer.write("{0}\n".format(text))
  except:
      print("Could not write to file {0}".format(filename))
  return None

def run(rawargs):
    arguments = docopt(doc, argv=rawargs, version='Get Image Dimensions v{0}'.format(Version))
    if not exists(arguments["--inputfile"]):
        print("The input file specified does not exist!")
        sys.exit(1)

    inputfile = pandas.read_csv(cleanPathString(arguments["--inputfile"]))
    tablelist = []
    for index, row in inputfile.iterrows():
        if exists(row["FILE"]):
            tablelist.append(pandas.read_csv(cleanPathString(row["FILE"])))
    masterdimfile = pandas.concat(tablelist)

    if len(masterdimfile) != 1:
        masterdimfile = masterdimfile.mode()

    summary = masterdimfile.head(1).squeeze()
    print(summary)
    mode_xdim = int(summary.loc["XDIM"])
    mode_ydim = int(summary.loc["YDIM"])
    mode_zdim = int(summary.loc["ZDIM"])

    mode_xpixdim = float(summary.loc["XPIXDIM"])
    mode_ypixdim = float(summary.loc["YPIXDIM"])
    mode_zpixdim = float(summary.loc["ZPIXDIM"])

    mode_xdimlog = int(summary.loc["XDIMLOG"])
    mode_ydimlog = int(summary.loc["YDIMLOG"])
    mode_zdimlog = int(summary.loc["ZDIMLOG"])

    #Perform calculations
    xTemplateDim = thresholdedVal(mode_xdimlog,128)
    yTemplateDim = thresholdedVal(mode_ydimlog,128)
    zTemplateDim = thresholdedVal(mode_zdimlog,128)

    modes = [mode_xpixdim, mode_ypixdim, mode_zpixdim]
    if hasRepeat(modes):
        isopixdim = max(set(modes), key=modes.count)
    else:
        isopixdim = max(modes)

    xTemplateVSize = mode_xdim * mode_xpixdim / float(xTemplateDim)
    yTemplateVSize = mode_ydim * mode_ypixdim / float(yTemplateDim)
    zTemplateVSize = mode_zdim * mode_zpixdim / float(zTemplateDim)

    if mode_xdim == xTemplateDim and mode_ydim == yTemplateDim and mode_zdim == zTemplateDim and mode_xpixdim == xTemplateVSize and mode_ypixdim == yTemplateVSize and mode_zpixdim == zTemplateVSize:
        resample = False
    else:
        resample = True

    writeToFile("{0} {1} {2}".format(xTemplateDim, yTemplateDim, zTemplateDim), arguments["--out_dim"])
    writeToFile("{0} {1} {2}".format(xTemplateVSize, yTemplateVSize, zTemplateVSize), arguments["--out_vsize"])
    writeToFile("{0} {0} {0}".format(isopixdim), arguments["--out_iso_vsize"])
    writeToFile("{0}".format(resample), arguments["--out_resample_bool"])

    sys.exit(0)


if __name__ == '__main__':
    args = sys.argv
    del args[0]
    run(args)
