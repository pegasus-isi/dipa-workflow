#!/usr/bin/env python


import sys
import os
import shutil
import subprocess
import pandas
import csv
import json
from docopt import docopt
from components.normalize import normalize

__version__ = "0.3b"
__doc__ = """Diffusion Image Processing and Analysis. v{0}

Usage:
 DIPA [options] (--input <path> | -i <path>) (--project <path> | -p <path>) (--site <site> | -s <site>) [--tier <level>...]

Components:
     Eddy Correction (Not Implemented)
     Orientation Checking (Not Implemented)
     Model Fitting (Not Implemented)
     Normalization (In Progress)
     ROI Extraction (Not Implemented)

Options:
     -h --help                       Show this screen. [default: False]
     -v --version                    Show the current version. [default: False]
     -i <path> --input <path>        The input spreadsheet, in csv format.
     -p <path> --project <path>      The output directory.
     -s <site> --site <site>         Site from site catalog to run the workflow.
     -k --keep_files                 Keep intermediate files. [default: False]
     -n <str> --name <str>           Add a custom name for the project. [default: Project]
     --correct_type                  (Eddy Correction) Select 'eddy' or 'eddy_correct'. [default: eddy]
     --fit_method                    (Model Fitting) Select either 'WLS' (weighted least squares) or 'OLS' (ordinary least squares) [default: WLS]
     --template                      (Normalization) Designate an original template (optional). [default: None]
     --similarity_metric <metric>    (Normalization) Registration type. [default: NMI]
     --species <species>             (Normalization) Species (either HUMAN, MONKEY, or RAT). [default: HUMAN]
     --rigid <rigidcount>            (Normalization) Number of rigid iterations. [default: 3]
     --affine <affinecount>          (Normalization) Number of affine iterations. [default: 3]
     --diffeo <diffeocount>          (Normalization) Number of diffeomorphic iterations. [default: 6]
     --tier <level>                  (Normalization) Normalize Hierarchichally. [default: PROJECT]
     --export_style <style>          (ROI Extraction) Specify 'long', 'wide' or 'both' [default: long]
""".format(__version__)

__arg_mapping__ = {
 "--input": "InputFile",
 "--project": "ProjectDir",
 "--name": "ProjectName",
 "--site": "Site",
 "--keep_files": "KeepFiles",
 "--correct_type": "CorrectType",
 "--fit_method": "FitMethod",
 "--template": "Template",
 "--similarity_metric": "SimmilarityMetric",
 "--species": "Species",
 "--rigid": "RigidIterations",
 "--affine": "AffineIterations",
 "--diffeo": "DiffeomorphicIterations",
 "--tier": "NormalizeHierarchy",
 "--export_style": "ExportStyle"
}

#some constants. can be updated via command line options
DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG = True #whether intermediate files make it to the output site or not


pegasus_config = "pegasus-config --python-dump"
config = subprocess.Popen(pegasus_config, stdout=subprocess.PIPE, shell=True).communicate()[0]
exec config

try:
    from Pegasus.DAX3 import *
except:
    print("DIPA was unable to find your installation of Pegasus. Ensure you have Pegasus and HTCondor installed.")
    sys.exit(1)

def clean_path(path):
  if path.startswith("~"):
    path = os.path.expanduser(path)
  realpath = os.path.realpath(path)
  return realpath

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [ byteify(element) for element in input ]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def read_json(jsonpath):
    if os.path.exists(jsonpath):
        with open(clean_path(jsonpath), "r") as jsonFile:
          jsondata = json.load(jsonFile)
          jsonFile.seek(0)
        return byteify(jsondata)
    else:
        print("Error! JSON File '{0}' does not exist! Exiting now.".format(clean_path(jsonpath)))
        sys.exit(1)


def create_workflow(options):
    """
    This generates a dipa dax
    """

    dax = ADAG( "dipa" )

    raw_matrix = pandas.read_csv(clean_path(options["InputFile"]))

    for index, row in raw_matrix.iterrows():
        try:
            shutil.copyfile(row["SPD"], options["ProjectDir"]+"/input/"+"{0}_spd.nii.gz".format(row["ID"]))
        except:
            print("Either your input csv was ill-formatted, or some number of files do not exist.")
            sys.exit(1)

    matrix = raw_matrix.copy()
    matrix["SPD"] = matrix["ID"].apply(lambda row: "{0}_spd.nii.gz".format(row))

    normalize_section = normalize(matrix, hierarchy=options["NormalizeHierarchy"], name=options["ProjectName"])
    dax = normalize_section.add_to_dax(dax)
    normalize_section.save_files(options["ProjectDir"]+"/input/")

    return dax


def system_call(command, environment={}):
  #A shorthand for running system processes, such as FSL commands
  p = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE, shell=False, env=environment)
  return p.stdout.read()

def main():

    # Obtain command-line arguments
    arguments = docopt(__doc__, version='DIPA v{0}'.format(__version__))
    options = {}
    for argument_flag, argument_value in __arg_mapping__.iteritems():
        options[argument_value] = arguments[argument_flag]

    #Setup of environmental variables and options
    options["InputFile"] = os.path.abspath(options["InputFile"])
    options["ProjectDir"] = os.path.abspath(options["ProjectDir"])
    options["DaxFile"] = options["ProjectDir"]+"/conf/master.dax"
    options["DipaDir"] = os.path.dirname(os.path.realpath(__file__))
    environment = dict(os.environ)
    jsonsettings = read_json(clean_path(options["DipaDir"]+"/conf/site_setup.json"))
    jsonsettings["DTITK_ROOT"] = os.path.abspath(jsonsettings["DTITK_ROOT"])
    jsonsettings["FSL_ROOT"] = os.path.abspath(jsonsettings["FSL_ROOT"])
    environment.update(jsonsettings)

    environment["ProjectDir"] = options["ProjectDir"]
    environment["DipaDir"] = options["DipaDir"]

    #Create some directories
    if not os.path.exists(options["ProjectDir"]):
        os.makedirs(options["ProjectDir"])
    for directory in [options["ProjectDir"]+"/input",options["ProjectDir"]+"/outputs",options["ProjectDir"]+"/working",]:
        if not os.path.exists(directory):
            os.mkdir(directory)
    if os.path.exists(options["ProjectDir"]+"/conf"):
        shutil.rmtree(options["ProjectDir"]+"/conf")
    shutil.copytree(options["DipaDir"]+"/conf",options["ProjectDir"]+"/conf")


    #Create the DAX
    dax = create_workflow(options)
    with open( options["DaxFile"],"w" ) as f:
        print "Writing DAX to {0}".format(options["DaxFile"])
        dax.writeXML(f)

    #Run pegasus-plan with these settings.
    os.chdir(options["ProjectDir"])
    pegasus_plan_command = "pegasus-plan --conf {ProjectDir}/conf/pegasusrc --sites {Site} --input-dir {ProjectDir}/input --output-site local --dir {ProjectDir}/working --relative-submit-dir ./condorsubmit --dax {DaxFile} --force --cleanup none --submit -vv".format(**options)
    print(pegasus_plan_command)

    system_call(pegasus_plan_command, environment)

if __name__ == "__main__":
    main()
