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

    # imagedim_jobs=[]
    # for individual in individuals:
    #     #add the location of _spd.nii.gz as Files in the DAX
    #     lfn = individual[0] + "_spd.nii.gz"
    #     file = File(lfn)
    #     file.addPFN( PFN("file://" + individual[1], "waisman"))
    #     dax.addFile( file )
    #
    #     # for each individual we construct a ImageDim_Project job
    #     imagedim_job = construct_image_dim_job( individual[0] )
    #     dax.addJob( imagedim_job )
    #     imagedim_jobs.append( imagedim_job )
    #
    # # create the CreateTemplate_Project job.
    # # requires some input files that dax generator creates currently image_dimension_files.csv initial_template_input.txt
    # image_dimension_files_csv = write_image_dimensions_file(input_dir, individuals)
    # file = File( os.path.basename(image_dimension_files_csv))
    # file.addPFN( PFN("file://" +image_dimension_files_csv, "waisman"))
    # dax.addFile( file )
    #
    # #write out initial_template_input.txt
    # initial_template_input_txt = write_initial_template_input_file(input_dir, individuals)
    # file = File( os.path.basename(initial_template_input_txt))
    # file.addPFN( PFN("file://" +initial_template_input_txt, "waisman"))
    # dax.addFile( file )
    #
    # template_project_job = construct_template_project_job( individuals )
    # dax.addJob( template_project_job )
    #
    # # the createtemplate job depends on all of imagedim jobs
    # for parent_job in imagedim_jobs:
    #     dax.depends( parent=parent_job, child=template_project_job )

    return dax


#
#
# def construct_image_dim_job( individual_id):
#
#     j = Job(name="Normalize_ImageDim",namespace="dipa", id="ID" + individual_id,)
#
#     #--id=ID103414 --inputfile=103414_spd.nii.gz --outputfile=103414_spd_dimensions.csv
#     args = []
#     args.append( "--id=ID" + individual_id  )
#     args.append( "--inputfile=" + individual_id + "_spd.nii.gz")
#     args.append( "--outputfile=" + individual_id + "_spd_dimensions.csv")
#
#
#     input_file = individual_id + "_spd.nii.gz"
#     j.uses( input_file , link=Link.INPUT)
#
#     #add the output log files
#     output_file = individual_id + "_spd_dimensions.csv"
#     j.uses( output_file, link=Link.OUTPUT, transfer=DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG)
#
#     # Finish job
#     j.addArguments(*args)
#
#     return j
#
#
# def construct_template_project_job( individuals):
#
#     j = Job(name="Normalize_CreateTemplate",namespace="dipa")
#
#     args = []
#
#     #add input files per individual
#     for individual in individuals:
#         individual_id = individual[0]
#         for suffix in ["_spd.nii.gz", "_spd_dimensions.csv"]:
#             input_file = individual_id + suffix
#             j.uses( input_file , link=Link.INPUT)
#
#     #add the fixed input files image_dimension_files.csv , initial_template_input.txt
#     for input_file in ["initial_template_input.txt", "image_dimension_files.csv" ]:
#         j.uses(  input_file , link=Link.INPUT)
#
#
#     #add the output files
#     for output_file in ["template_vsize.txt", "template_resample_bool.txt", "template_iso_vsize.txt", "template_dim.txt", "initial_template_orig.nii.gz", "initial_template.nii.gz" ,"mean_rigid0.nii.gz"]:
#         j.uses( output_file, link=Link.OUTPUT, transfer=DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG)
#
#     # Finish job
#     j.addArguments("--lookupfile", "image_dimension_files.csv",
#                    "--templateinputsfile", "initial_template_input.txt",
#                    "--resamplefile", "template_resample_bool.txt",
#                    "--vsizefile", "template_vsize.txt",
#                    "--dimsizefile", "template_dim.txt",
#                    "--orig", "initial_template_orig.nii.gz",
#                    "--initial", "initial_template.nii.gz",
#                    "--rigid", "mean_rigid0.nii.gz",)
#
#     return j
#
# def readNormalizeFile( input_file ):
#     """
#     Reads in the normalize input file and returns a list of tuples with id's and file locations.
#     :param input_file:
#     :return:
#     """
#
#     print input_file
#     result = []
#     with open( input_file, 'rb') as f:
#         reader = csv.reader(f)
#         result = list(reader)
#
#     if len(result) == 0:
#         #empty file. just return
#         return result
#
#     #remove the header if specified
#     header = result[0]
#     if header[0] == "ID":
#         #remove the first entry from result list
#         del result[0]
#
#     return result
#
# def write_image_dimensions_file( directory, individuals ):
#
#     file = open( directory + "/" + "image_dimension_files.csv", 'w')
#     file.write("ID,File" + "\n")
#     for individual in individuals:
#         file.write( individual[0] + "," + individual[0] + "_spd_dimensions.csv" + "\n")
#     file.close()
#     return file.name
#
# def write_initial_template_input_file( directory, individuals ):
#
#     file = open( directory + "/" + "initial_template_input.txt", 'w')
#     for individual in individuals:
#         file.write( individual[0] + "_spd.nii.gz" + "\n")
#     file.close()
#     return file.name

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
