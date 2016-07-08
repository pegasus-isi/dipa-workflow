#!/usr/bin/env python


import sys
import os
import optparse
import subprocess
import csv


#some constants. can be updated via command line options
DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG = True #whether intermediate files make it to the output site or not


pegasus_config = "pegasus-config --python-dump"
config = subprocess.Popen(pegasus_config, stdout=subprocess.PIPE, shell=True).communicate()[0]
exec config


from Pegasus.DAX3 import *

def getDAX( normalize_file, input_dir ):
    """
    This generates a dipa dax
    """

    dax = ADAG( "dipa" )

    individuals = readNormalizeFile( normalize_file )

    imagedim_jobs=[]
    for individual in individuals:
        #add the location of _spd.nii.gz as Files in the DAX
        lfn = individual[0] + "_spd.nii.gz"
        file = File(lfn)
        file.addPFN( PFN("file://" + individual[1], "waisman"))
        dax.addFile( file )

        # for each individual we construct a ImageDim_Project job
        imagedim_job = construct_image_dim_job( individual[0] )
        dax.addJob( imagedim_job )
        imagedim_jobs.append( imagedim_job )

    # create the CreateTemplate_Project job.
    # requires some input files that dax generator creates currently image_dimension_files.csv initial_template_input.txt
    image_dimension_files_csv = write_image_dimensions_file(input_dir, individuals)
    file = File( os.path.basename(image_dimension_files_csv))
    file.addPFN( PFN("file://" +image_dimension_files_csv, "waisman"))
    dax.addFile( file )

    #write out initial_template_input.txt
    initial_template_input_txt = write_initial_template_input_file(input_dir, individuals)
    file = File( os.path.basename(initial_template_input_txt))
    file.addPFN( PFN("file://" +initial_template_input_txt, "waisman"))
    dax.addFile( file )

    template_project_job = construct_template_project_job( individuals )
    dax.addJob( template_project_job )

    # the createtemplate job depends on all of imagedim jobs
    for parent_job in imagedim_jobs:
        dax.depends( parent=parent_job, child=template_project_job )

    return dax




def construct_image_dim_job( individual_id):

    j = Job(name="ImageDim_Project",namespace="dipa", id="ID" + individual_id,)

    #--id=ID103414 --inputfile=103414_spd.nii.gz --outputfile=103414_spd_dimensions.csv
    args = []
    args.append( "--id=ID" + individual_id  )
    args.append( "--inputfile=" + individual_id + "_spd.nii.gz")
    args.append( "--outputfile=" + individual_id + "_spd_dimensions.csv")


    input_file = individual_id + "_spd.nii.gz"
    j.uses( input_file , link=Link.INPUT)

    #add the output log files
    output_file = individual_id + "_spd_dimensions.csv"
    j.uses( output_file, link=Link.OUTPUT, transfer=DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG)

    # Finish job
    j.addArguments(*args)

    return j


def construct_template_project_job( individuals):

    j = Job(name="CreateTemplate_Project",namespace="dipa")

    args = []

    #add input files per individual
    for individual in individuals:
        individual_id = individual[0]
        for suffix in ["_spd.nii.gz", "_spd_dimensions.csv"]:
            input_file = individual_id + suffix
            j.uses( input_file , link=Link.INPUT)

    #add the fixed input files image_dimension_files.csv , initial_template_input.txt
    for input_file in ["initial_template_input.txt", "image_dimension_files.csv" ]:
        j.uses(  input_file , link=Link.INPUT)


    #add the output files
    for output_file in ["template_vsize.txt", "template_resample_bool.txt", "template_iso_vsize.txt", "template_dim.txt", "initial_template_orig.nii.gz", "initial_template.nii.gz" ,"mean_rigid0.nii.gz"]:
        j.uses( output_file, link=Link.OUTPUT, transfer=DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG)

    # Finish job
    j.addArguments(*args)

    return j

def readNormalizeFile( input_file ):
    """
    Reads in the normalize input file and returns a list of tuples with id's and file locations.
    :param input_file:
    :return:
    """

    print input_file
    result = []
    with open( input_file, 'rb') as f:
        reader = csv.reader(f)
        result = list(reader)

    if len(result) == 0:
        #empty file. just return
        return result

    #remove the header if specified
    header = result[0]
    if header[0] == "ID":
        #remove the first entry from result list
        del result[0]

    return result

def write_image_dimensions_file( directory, individuals ):

    file = open( directory + "/" + "image_dimension_files.csv", 'w')
    file.write("ID,File" + "\n")
    for individual in individuals:
        file.write( individual[0] + "," + individual[0] + "_spd_dimensions.csv" + "\n")
    file.close()
    return file.name

def write_initial_template_input_file( directory, individuals ):

    file = open( directory + "/" + "initial_template_input.txt", 'w')
    for individual in individuals:
        file.write( individual[0] + "_spd.nii.gz" + "\n")
    file.close()
    return file.name

def main():
    # Configure command line option parser
    usage = '%s [options]' % sys.argv[0]
    description = '%s [i]'    % sys.argv[0]

    parser = optparse.OptionParser (usage=usage, description=description)

    parser.add_option("-i", "--input-file", action="store", type="str", dest="normalize_file",  help="csv file containing subjects to normalize")
    parser.add_option("-I", "--input-dir",  action="store", type="str", dest="input_dir",  help="the input directory where input files for the workflow generated by dax generator are placed")
    parser.add_option("-o", "--output-dax", action="store", type="str", dest="daxfile", help="the output dax file to write")

    #Parsing command-line options
    (options, args) = parser.parse_args ()

    if options.normalize_file is None:
        parser.error( "Specify the -i option to specify the input cvs file containing subjects to normalize")

    if options.daxfile is None:
        parser.error( "Specify the -o option to specify the output dax file ")

    if options.input_dir is None:
        #set to input directory in current working dir
        options.input_dir = os.path.abspath( os.curdir + "./input" )
        print options.input_dir

    try:
        os.stat(options.input_dir)
    except:
        os.mkdir(options.input_dir)
    options.input_dir = os.path.abspath( options.input_dir)

    dax = getDAX( options.normalize_file, options.input_dir )

    f = open( options.daxfile,"w" )
    print "Writing DAX to %s" %(os.path.abspath( options.daxfile ) )
    dax.writeXML(f)
    f.close()

    # dup the dax to stdout for time being
    #dax.writeXML(sys.stdout)

if __name__ == "__main__":
    main()
