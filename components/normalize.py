#!/bin/python
from Pegasus.DAX3 import *
import sys

class normalize(object):
    """
    Normalize component of DIPA.
    Uses DTI-TK to normalize subjects to an iteratively improved template, or a predefined one.
    matrix is assumed to be a pandas dataframe. "hierarchy" is a list referencing headers in the matrix.
    """
    def __init__(self, matrix, hierarchy=["PROJECT", "ID"], name="Project", template=None, similarity_metric="NMI", species="Human", rigid=3, affine=3, diffeomorphic=6):
        self.matrix = matrix
        self.hierarchy = hierarchy
        if "ID" not in self.hierarchy:
            self.hierarchy.append("ID")
        if "PROJECT" not in self.hierarchy:
            self.hierarchy = ["PROJECT"] + self.hierarchy
        self.name = name
        self.template = template
        self.similarity_metric = similarity_metric
        self.species = species
        self.rigid = rigid
        self.affine = affine
        self.diffeomorphic = diffeomorphic
        try:
            if "PROJECT" not in self.matrix.columns:
                self.matrix["PROJECT"] = self.name
            self.matrix = self.matrix[hierarchy + ["SPD"]]
        except:
            print("The spreadsheet you supplied did not have columns for the hierarchy specified. Exiting.")
            sys.exit(1)
        self.__plan__()

    def __plan_tier__(self, matrix, hierarchies, dax):
        if len(hierarchies) > 2:
            child_matrix_set = matrix[hierarchies[1:]]
            for child_matrix in child_matrix_set.groupby(hierarchies[1])
                self.__plan_tier__(child_matrix, hierarchies[1:], dax)

        #Plan normalization here


    def add_to_dax(self, dax):
        return dax

class normalize_ImageDim(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, hierarchy, matrix):
        self.job_id = "Normalize_ImageDim_{0}-{1}".format(source_tier, source_id)
        self.pegasus_job = Job(name="Normalize_ImageDim", namespace="dipa", id=self.job_id)
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_id == hierarchy[-1]:
            inputfile = matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"]
        else:
            inputfile = "{0}-{1}_template.nii.gz".format(source_tier, source_id)
        outputfile = "{0}_dimensions.nii.gz".format(source_id)
        args = ["--id={0}".format(source_id), "--inputfile="+inputfile, "--outputfile="+outputfile]
        self.pegasus_job.uses(inputfile, link=Link.INPUT)
        self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG)
        self.addArguments(*args)

class normalize_CreateTemplate(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix):
        self.job_id = "Normalize_CreateTemplate_{0}-{1}".format(template_tier, template_id)
        self.pegasus_job = Job(name="Normalize_CreateTemplate", namespace="dipa", id=self.job_id)

        self.pegasus_job.addArguments(
                       "--lookupfile", "{0}_dimension_files.csv".format(template_id),
                       "--templateinputsfile", "{0}_initial_template_input.txt".format(template_id),
                       "--resamplefile", "{0}_template_resample_bool.txt".format(template_id),
                       "--vsizefile", "{0}_template_vsize.txt".format(template_id),
                       "--dimsizefile", "{0}_template_dim.txt".format(template_id),
                       "--orig", "{0}_initial_template_orig.nii.gz".format(template_id),
                       "--initial", "{0}_initial_template.nii.gz".format(template_id),
                       "--rigid", "{0}_mean_rigid0.nii.gz".format(template_id))

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])


        input_files = ["{0}_dimension_files.csv".format(template_id),
                       "{0}_initial_template_input.txt".format(template_id)]

        output_files = ["{0}_template_resample_bool.txt".format(template_id),
                        "{0}_template_vsize.txt".format(template_id),
                        "{0}_template_dim.txt".format(template_id),
                        "{0}_initial_template_orig.nii.gz".format(template_id),
                        "{0}_initial_template.nii.gz".format(template_id),
                        "{0}_mean_rigid0.nii.gz".format(template_id)]

        if source_tier == "ID":
            input_files.append(list(matrix[matrix[template_tier] == template_id]["SPD"]))
        else:
            for source_id in source_ids:
                input_files.append("{0}-{1}_template.nii.gz".format(source_tier, source_id))
        for source_id in source_ids:
            input_files.append("{0}_dimensions.nii.gz".format(source_id))

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=DEFAULT_INTERMEDIATE_FILES_TRANSFER_FLAG)
