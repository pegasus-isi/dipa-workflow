#!/usr/bin/env python



import os, sys, pandas, math, nibabel
from docopt import docopt

Version = "0.1"

doc = """
Get Image Dimensions, Version {0}.

Usage:
    getimagedim.py [options] --id=<ID> --inputfile=<FILE> --outputfile=<FILE>

Options:
    -h --help                Show this screen.
    -v --version             Show version.
    --id=<ID>                Specify the ID for the ID column
    --inputfile=<FILE>       Input File (path).
    --outputfile=<FILE>      Output File (path).
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

# def systemCall(command):
#   #A shorthand for running system processes, such as FSL commands
#   p = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, shell=False)
#   return p.stdout.read()

def run(rawargs):
    arguments = docopt(doc, argv=rawargs, version='Get Image Dimensions v{0}'.format(Version))
    if not exists(arguments["--inputfile"]):
        print("The input file specified does not exist!")
        sys.exit(1)

    try:
        image = nibabel.load(arguments["--inputfile"])

        xdim = image.shape[0]
        ydim = image.shape[1]
        zdim = image.shape[2]
        xpixdim = image._header["pixdim"][1]
        ypixdim = image._header["pixdim"][2]
        zpixdim = image._header["pixdim"][3]

        xdimLogRounded = math.pow(2, round(math.log(xdim, 2)))
        ydimLogRounded = math.pow(2, round(math.log(ydim, 2)))
        zdimLogRounded = math.pow(2, round(math.log(zdim, 2)))

        dimdataframe = pandas.DataFrame([{"ID": arguments["--id"], "XDIM": xdim, "YDIM": ydim, "ZDIM": zdim, "XPIXDIM": xpixdim, "YPIXDIM": ypixdim, "ZPIXDIM": zpixdim, "XDIMLOG": xdimLogRounded, "YDIMLOG": ydimLogRounded, "ZDIMLOG": zdimLogRounded}])
        print(dimdataframe)
        dimdataframe.to_csv(arguments["--outputfile"], index=False)

    except:
        print("Could not determine the necessary image dimensions.")
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    args = sys.argv
    del args[0]
    run(args)
