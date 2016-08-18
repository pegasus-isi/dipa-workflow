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
     --correct_type <str>            (Preprocess) Select 'eddy' or 'eddy_correct'. [default: eddy]
     --correct_topup                 (Preprocess) Use topup, and feed this into eddy. [default: False]
     --correct_eddy_flm <str>        (Preprocess) First level EC model for eddy ('linear','quatratic', or 'cubic'). [default: quadratic]
     --correct_eddy_slm <str>        (Preprocess) Second level EC model for eddy ('none','linear', or 'quatratic'). [default: 'none']
     --correct_eddy_fwhm <num>       (Preprocess) FWHM for conditioning filter when estimating the parameters for eddy. [default: 0]
     --correct_eddy_niters <int>     (Preprocess) Number of iterations for eddy [default: 5]
     --correct_eddy_fep	             (Preprocess) Fill empty planes in x- or y-directions in eddy
     --correct_eddy_interp           (Preprocess) Interpolation model for estimation step in eddy and eddy_correct ('spline' or 'trilinear') [default: spline]
     --correct_eddy_resamp           (Preprocess) Final resampling method ('jac' or 'lsr') [default: jac]
     --correct_eddy_nvoxhp <int>     (Preprocess) Number of voxels used to estimate the hyperparameters [default: 1000]
     --correct_eddy_ff	             (Preprocess) Fudge factor for hyperparameter error variance [default: 10.0]
     --correct_eddy_no_sep_offs	     (Preprocess) Do NOT attempt to separate field offset from subject movement [default: False]
     --correct_eddy_dont_peas	     (Preprocess) Do NOT perform a post-eddy alignment of shells [default: False]
     --no_orient_check               (Preprocess) Do NOT generate output images showing orientation of images. [default: False]
     --fit_method <str>              (Preprocess) Select either 'WLS' (weighted least squares) or 'OLS' (ordinary least squares) [default: WLS]
     --template <path>               (Normalization) Designate an original template (optional). [default: None]
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
 "--similarity_metric": "SimilarityMetric",
 "--species": "Species",
 "--rigid": "RigidIterations",
 "--affine": "AffineIterations",
 "--diffeo": "DiffeomorphicIterations",
 "--tier": "NormalizeHierarchy",
 "--export_style": "ExportStyle"
}

#some constants. can be updated via command line options
#DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG = True #whether intermediate files make it to the output site or not
#Replaced with --keep_files flag.


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
    try:
        matrix = pandas.read_csv(clean_path(options["InputFile"]))
    except:
        print("Could not find the input file specified here: "+ clean_path(options["InputFile"]))
        sys.exit(1)

    # print("Adding preprocessing to workflow.")
    # preprocessing_section = preprocess(matrix, hierarchy=options["NormalizeHierarchy"],
    #                                            name=options["ProjectName"],
    #                                            eddy_correction=options["EddyCorrection"],
    #                                            orient_check=options["OrientCheck"],
    #                                            fit_method=options["FitMethod"],
    #                                            is_shelled=options["Shelled"])
    # dax = preprocessing_section.add_to_dax(dax)

    print("Adding normalization to workflow.")
    normalize_section = normalize(matrix, hierarchy=options["NormalizeHierarchy"],
                                          name=options["ProjectName"],
                                          template=options["Template"],
                                          rigid=int(options["RigidIterations"]),
                                          affine=int(options["AffineIterations"]),
                                          diffeomorphic=int(options["DiffeomorphicIterations"]),
                                          transferflag=options["KeepFiles"],
                                          similarity_metric=options["SimilarityMetric"],
                                          species=options["Species"])
    dax = normalize_section.add_to_dax(dax)

    #Perform Linkages
    # print("Linking preprocesssing to normalization in workflow.")
    # for index, end_preprocessing_step in enumerate(preprocesssing_section.final_steps):
    #     dax.depends(parent=end_preprocessing_step.pegasus_job, child=normalize_section.initial_steps[index].pegasus_job)

    try:
        # for index, mapping in preprocessing_section.mappings.iterrows():
        #     shutil.copyfile(mapping["SOURCE"], options["ProjectDir"]+"/input/"+mapping["DESTINATION"])
        for index, mapping in normalize_section.mappings.iterrows():
            shutil.copyfile(mapping["SOURCE"], options["ProjectDir"]+"/input/"+mapping["DESTINATION"])
    except:
        print("Either your input csv was ill-formatted, or some number of files do not exist.")
        sys.exit(1)
    if options["Template"] != None:
        try:
            shutil.copyfile(options["Template"], options["ProjectDir"]+"/input/"+options["ProjectName"]+"_template_orig.nii.gz")
        except:
            print("Error: Could not copy template file to project directory.")
            sys.exit(1)
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
            print("Template file could not be found. Check that it exists at {0}".format(options["Template"]))

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
    environment.update(jsonsettings)

    environment["ProjectDir"] = options["ProjectDir"]
    environment["DipaDir"] = options["DipaDir"]

    #Create some directories
    if not os.path.exists(options["ProjectDir"]):
        print("Setting up directories.")
        os.makedirs(options["ProjectDir"])
    for directory in [options["ProjectDir"]+"/input",options["ProjectDir"]+"/outputs",options["ProjectDir"]+"/working",]:
        if not os.path.exists(directory):
            os.mkdir(directory)
    if os.path.exists(options["ProjectDir"]+"/conf"):
        if os.path.exists(options["ProjectDir"]+"/conf/input.csv"):
            with open(options["ProjectDir"]+"/conf/input.csv") as f1:
                with open(options["InputFile"]) as f2:
                    if f1.read() == f2.read():
                        options["ChangedDax"] = True
        shutil.rmtree(options["ProjectDir"]+"/conf")
    shutil.copytree(options["DipaDir"]+"/conf",options["ProjectDir"]+"/conf")
    #os.copyfile(options["InputFile"], )


    #Create the DAX
    print("Creating the workflow.")
    dax = create_workflow(options)
    print("Saving the workflow")
    with open( options["DaxFile"],"w" ) as f:
        print "Writing DAX to {0}".format(options["DaxFile"])
        dax.writeXML(f)

    #Run pegasus-plan with these settings.
    os.chdir(options["ProjectDir"])
    print("Submitting the workflow")
    if os.listdir("{ProjectDir}/outputs".format(**options)) == []:
        pegasus_command = "pegasus-plan --conf {ProjectDir}/conf/pegasusrc --sites {Site} --input-dir {ProjectDir}/input --output-site local --dir {ProjectDir}/working --relative-submit-dir ./condorsubmit --dax {DaxFile} --force --cleanup none --submit -vv".format(**options)
    else:
        pegasus_command = "pegasus-run {ProjectDir}/working/condorsubmit".format(**options)
    pegasus_graphviz_command = "pegasus-graphviz {DaxFile} -o {DotFile} -s -l id -f".format(**options)
    dot_command = "dot -Tpdf {DotFile} -o {PDFFile}".format(**options)
    system_call(pegasus_command, environment)
    system_call(pegasus_graphviz_command, environment)
    try:
        system_call(dot_command, environment)
    except:
        print("WARNING: Could not save a pdf verison of the workflow.")

if __name__ == "__main__":
    main()
