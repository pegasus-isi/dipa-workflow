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
from components.preprocess import preprocess
from utility.console import Console, Notice, Progress
from utility.parse import matrixparser

__version__ = "0.3b"
__doc__ = """Diffusion Image Processing and Analysis. v{0}

Usage:
 DIPA [options] (--input <path> | -i <path>) (--project <path> | -p <path>) (--site <site> | -s <site>) [--tier <level>...]

Components:
     Preprocess - Eddy Correction (In Progress)
     Preprocess - Orientation Checking (In Progress)
     Preprocess - Model Fitting (In Progress)
     Normalization (In Testing)
     ROI Extraction (Not Implemented)

Options:
     -h --help                       Show this screen. [default: False]
     -v --version                    Show the current version. [default: False]
     -i <path> --input <path>        The input spreadsheet, in csv format.
     -p <path> --project <path>      The output directory.
     -s <site> --site <site>         Site from site catalog to run the workflow.
     -k --keep_files                 Keep intermediate files. [default: False]
     -n <str> --name <str>           Add a custom name for the project. [default: Project]
     --verbosity <str>               Specify verbosity from ('log', 'alert', 'warning', 'error'). [default: log]
     --correct_type <str>            (Preprocess) Select 'eddy' or 'eddy_correct'. [default: eddy]
     --correct_topup                 (Preprocess) Use topup, and feed this into eddy. [default: False]
     --correct_eddy_flm <str>        (Preprocess) First level EC model for eddy ('linear','quatratic', or 'cubic'). [default: quadratic]
     --correct_eddy_slm <str>        (Preprocess) Second level EC model for eddy ('none','linear', or 'quatratic'). [default: 'none']
     --correct_eddy_fwhm <num>       (Preprocess) FWHM for conditioning filter when estimating the parameters for eddy. [default: 0]
     --correct_eddy_niters <int>     (Preprocess) Number of iterations for eddy [default: 5]
     --correct_eddy_fep	             (Preprocess) Fill empty planes in x- or y-directions in eddy [default: False]
     --correct_eddy_interp <str>     (Preprocess) Interpolation model for estimation step in eddy and eddy_correct ('spline' or 'trilinear') [default: spline]
     --correct_eddy_resamp <str>     (Preprocess) Final resampling method ('jac' or 'lsr') [default: jac]
     --correct_eddy_nvoxhp <int>     (Preprocess) Number of voxels used to estimate the hyperparameters [default: 1000]
     --correct_eddy_ff <float>	     (Preprocess) Fudge factor for hyperparameter error variance [default: 10.0]
     --correct_eddy_no_sep_offs	     (Preprocess) Do NOT attempt to separate field offset from subject movement [default: False]
     --correct_eddy_dont_peas	     (Preprocess) Do NOT perform a post-eddy alignment of shells [default: False]
     --orient_check <bool>           (Preprocess) Do generate output images showing orientation of images. [default: True]
     --fit_type <str>                (Preprocess) Select either 'dipy' or 'camino' [default: dipy]
     --fit_method <str>              (Preprocess) Select either 'WLS' (weighted least squares) or 'OLS' (ordinary least squares) [default: WLS]
     --shelled <bool>                (Preprocess) Either 'True' or 'False'. Specify whether data is shelled. [default: True]
     --multishelled <bool>           (Preprocess) Either 'True' or 'False'. Specify whether data is multi-shelled. [default: True]
     --template <path>               (Normalization) Designate an original template (optional). [default: None]
     --similarity_metric <metric>    (Normalization) Registration type. [default: NMI]
     --species <species>             (Normalization) Species (either HUMAN, MONKEY, or RAT). [default: HUMAN]
     --rigid <rigidcount>            (Normalization) Number of rigid iterations. [default: 3]
     --affine <affinecount>          (Normalization) Number of affine iterations. [default: 3]
     --diffeo <diffeocount>          (Normalization) Number of diffeomorphic iterations. [default: 6]
     --tier <level>                  (Normalization) Normalize Hierarchichally. Repeat as needed in order of increasing specificity [default: PROJECT]
     --export_style <style>          (ROI Extraction) Specify 'long', 'wide' or 'both' [default: long]
""".format(__version__)

__arg_mapping__ = {
 "--input": "InputFile",
 "--project": "ProjectDir",
 "--name": "ProjectName",
 "--site": "Site",
 "--keep_files": "KeepFiles",
 "--verbosity": "Verbosity",
 "--tier": "Hierarchy",
}

for component in [preprocess, normalize]:
    __arg_mapping__.update(component.get_arg_mappings())

pegasus_config = "pegasus-config --python-dump"
config = subprocess.Popen(pegasus_config, stdout=subprocess.PIPE, shell=True).communicate()[0]
exec config

try:
    from Pegasus.DAX3 import *
except:
    proto_console = Console()
    proto_console.log(Notice("Error", "DIPA was unable to find your installation of Pegasus. Ensure you have Pegasus and HTCondor installed."))
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
        console.log(Notice("Error", "JSON File '{0}' does not exist! Exiting now.".format(clean_path(jsonpath))))
        sys.exit(1)


def create_workflow(options, console):
    """
    This generates a dipa dax
    """
    if options["ProjectName"] == "Project":
        dax = ADAG( "DIPA")
    else:
        dax = ADAG( "DIPA-"+options["ProjectName"])
    try:
        matrix = pandas.read_csv(clean_path(options["InputFile"]))

    except:
        console.log(Notice("Error", "Could not find the input file specified at "+ clean_path(options["InputFile"])))
        sys.exit(1)

    console.log(Notice("Log", "Parsing input file."))
    parser = matrixparser(matrix, options["Hierarchy"], name=options["ProjectName"], eddy_correction=options["CorrectType"], is_shelled=options["Shelled"], template=options["Template"])
    for warning in parser.warnings:
        console.log(warning)
    if parser.is_valid:
        matrix = parser.matrix
        options["Hierarchy"] = parser.hierarchy
        options["CorrectType"] = parser.eddy_correction
        #print(matrix)
    else:
        sys.exit(1)

    #Preprocessing
    console.log(Notice("Log", "Adding preprocessing to workflow."))
    #print(options)
    preprocessing_section = preprocess(matrix, hierarchy=options["Hierarchy"], name=options["ProjectName"], correct_type=options["CorrectType"],
                                               orient_check=options["OrientationCheck"], fit_type=options["FitType"], fit_method=options["FitMethod"], eddy_interp=options["EddyInterp"],
                                               is_shelled=options["Shelled"], multishelled=options["Multishelled"], topup=options["Topup"], eddy_flm=options["EddyFLM"], eddy_slm=options["EddySLM"], eddy_fwhm=options["EddyFWHM"],
                                               eddy_niters=options["EddyNiters"], eddy_fep=options["EddyFEP"], eddy_resample=options["EddyResample"], eddy_nvoxhp=options["EddyNvoxhp"], eddy_ff=options["EddyFF"],
                                               eddy_no_sep_offs=options["EddyNoSepOffs"], eddy_dont_peas=options["EddyDontPeas"], transferflag=options["KeepFiles"])
    for message in preprocessing_section.messages:
        console.log(message)
    preprocessing_section.reset_messages()

    progressbar = Progress(console, "Adding preprocessing jobs", count=20, limited=False)
    progressbar.start()
    dax = preprocessing_section.add_to_dax(dax, progressbar)
    progressbar.close("Normal")

    #Normalization
    console.log(Notice("Log", "Adding normalize to workflow."))
    normalize_section = normalize(matrix, hierarchy=options["Hierarchy"],
                                          name=options["ProjectName"],
                                          template=options["Template"],
                                          rigid=int(options["RigidIterations"]),
                                          affine=int(options["AffineIterations"]),
                                          diffeomorphic=int(options["DiffeomorphicIterations"]),
                                          transferflag=options["KeepFiles"],
                                          similarity_metric=options["SimilarityMetric"],
                                          species=options["Species"])
    for message in normalize_section.messages:
        console.log(message)
    normalize_section.reset_messages()

    progressbar = Progress(console, "Adding normalize jobs", count=20, limited=False)
    progressbar.start()
    dax = normalize_section.add_to_dax(dax, progressbar)
    progressbar.close("Normal")

    console.log(Notice("Log", "Performing linkages across components."))
    subset_ids = list(matrix["FULL"].unique())
    progressbar = Progress(console, "Linking preprocessing to normalization", count=len(subset_ids))
    progressbar.start()
    for index, subset_id in enumerate(subset_ids):
        fit_job_id = "{0}_Preprocess_Fit".format(subset_id)
        normalize_job_id = "{0}_Normalize_ImageDim".format(subset_id)
        dax.depends(parent=fit_job_id, child=normalize_job_id)
        progressbar.update(index+1)
    progressbar.close("Normal")

    progressbar = Progress(console, "Copying source files.", count=len(parser.mappings))
    progressbar.start()
    for index, mapping in parser.mappings.iterrows():
        try:
            shutil.copyfile(mapping["SOURCE"], options["ProjectDir"]+"/input/"+mapping["DESTINATION"])
            progressbar.update(index+1)
        except:
            progressbar.add_warning(Notice("Error", "Could not copy file {0} to {1}".format(mapping["SOURCE"], options["ProjectDir"]+"/input/"+mapping["DESTINATION"])))
    progressbar.close("Normal")
    print("Saving files.")
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

    #Create a console object
    console = Console(options["Verbosity"].title())
    console.log(Notice("Log", "Starting DIPA-WORKFLOW"))

    #Setup of environmental variables and options
    options["InputFile"] = os.path.abspath(options["InputFile"])
    options["ProjectDir"] = os.path.abspath(options["ProjectDir"])
    if options["Template"] in ["None", None, "False",False]:
        options["Template"] = None
    else:
        print(options["Template"])
        if os.path.exists(os.path.abspath(options["Template"])):
            options["Template"] = os.path.abspath(options["Template"])
        else:
            print()
            console.log(Notice("Error", "Template file could not be found. Check that it exists at {0}".format(options["Template"])))

    options["ProjectDir"] = os.path.abspath(options["ProjectDir"])
    options["DaxFile"] = options["ProjectDir"]+"/conf/master.dax"
    options["DotFile"] = options["ProjectDir"]+"/conf/master.dot"
    options["PDFFile"] = options["ProjectDir"]+"/conf/master.pdf"
    options["ChangedDax"] = False
    options["DipaDir"] = os.path.dirname(os.path.realpath(__file__))
    environment = dict(os.environ)
    jsonsettings = read_json(clean_path(options["DipaDir"]+"/conf/site_setup.json"))
    jsonsettings["DTITK_ROOT"] = os.path.abspath(jsonsettings["DTITK_ROOT"])
    jsonsettings["FSL_ROOT"] = os.path.abspath(jsonsettings["FSL_ROOT"])
    jsonsettings["CAMINO_ROOT"] = os.path.abspath(jsonsettings["CAMINO_ROOT"])
    jsonsettings["PYTHON_PATH"] = os.path.abspath(jsonsettings["PYTHON_PATH"])
    environment.update(jsonsettings)

    environment["ProjectDir"] = options["ProjectDir"]
    environment["DipaDir"] = options["DipaDir"]

    #Create directories
    progressbar = Progress(console, "Setting up directories", count=4)
    progressbar.start()
    for index, directory in enumerate([options["ProjectDir"], options["ProjectDir"]+"/input", options["ProjectDir"]+"/outputs", options["ProjectDir"]+"/working",]):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                progressbar.update(index+1)
            except:
                progressbar.close("Error")
                progressbar.add_warning(Notice("Error", "Could not make directory at {0}".format(directory)))
        else:
            progressbar.add_warning(Notice("Alert", "Directory already exists: {0}".format(directory)))
            progressbar.update(index+1)
    progressbar.close("Normal")

    if os.path.exists(options["ProjectDir"]+"/conf"):
        if os.path.exists(options["ProjectDir"]+"/conf/input.csv"):
            with open(options["ProjectDir"]+"/conf/input.csv") as f1:
                with open(options["InputFile"]) as f2:
                    if f1.read() == f2.read():
                        options["ChangedDax"] = True
        shutil.rmtree(options["ProjectDir"]+"/conf")
    shutil.copytree(options["DipaDir"]+"/conf",options["ProjectDir"]+"/conf")
    shutil.copyfile(options["InputFile"], options["ProjectDir"]+"/conf/input.csv")


    #Create the DAX
    dax = create_workflow(options, console)
    console.log(Notice("Log", "Saving the workflow"))
    with open( options["DaxFile"],"w" ) as f:
        console.log(Notice("Log", "Writing DAX to {0}".format(options["DaxFile"])))
        dax.writeXML(f)

    #Run pegasus-plan with these settings.
    os.chdir(options["ProjectDir"])
    console.log(Notice("Log", "Submitting the workflow"))
    if os.listdir("{ProjectDir}/outputs".format(**options)) == [] or options["ChangedDax"] == True:
        pegasus_command = "pegasus-plan --conf {ProjectDir}/conf/pegasusrc --sites {Site} --input-dir {ProjectDir}/input --output-site local --dir {ProjectDir}/working --relative-submit-dir ./condorsubmit --dax {DaxFile} --cleanup none --submit -vv".format(**options)
    else:
        pegasus_command = "pegasus-run {ProjectDir}/working/condorsubmit".format(**options)
    pegasus_graphviz_command = "pegasus-graphviz {DaxFile} -o {DotFile} -s -l id".format(**options)
    dot_command = "dot -Tpdf {DotFile} -o {PDFFile}".format(**options)
    system_call(pegasus_command, environment)
    system_call(pegasus_graphviz_command, environment)
    try:
        system_call(dot_command, environment)
    except:
        console.log(Notice("Error", "Could not save a pdf verison of the workflow."))

if __name__ == "__main__":
    main()
