#!/bin/python
from Pegasus.DAX3 import *
import sys
import pandas

class normalize(object):
    """
    Normalize component of DIPA.
    Uses DTI-TK to normalize subjects to an iteratively improved template, or a predefined one.
    matrix is assumed to be a pandas dataframe. "hierarchy" is a list referencing headers in the matrix.
    """
    def __init__(self, matrix, hierarchy=["PROJECT", "ID"], name="Project", template=None, similarity_metric="NMI", species="Human", rigid=3, affine=3, diffeomorphic=6, transferflag=True):
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
        self.files = {}
        self.transferflag = transferflag
        if "PROJECT" not in self.matrix.columns:
            self.matrix["PROJECT"] = self.name
        try:
            self.matrix = self.matrix[self.hierarchy + ["SPD"]]
        except:
            print("The spreadsheet you supplied did not have columns for the hierarchy specified. Exiting.")
            sys.exit(1)

    def __plan_tier__(self, matrix, hierarchies, dax):

        #Plan normalization here
        template_tier = hierarchies[0]
        template_id = matrix[hierarchies[0]].unique()[0]
        source_tier = hierarchies[1]
        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])
        ImageDim_Jobs = []
        CreateTemplate_Jobs = []

        #ImageDim
        for source_id in source_ids:
            imagedimjob = normalize_ImageDim(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, transferflag=self.transferflag)
            self.files.update(imagedimjob.files)
            ImageDim_Jobs.append(imagedimjob)

        #CreateTemplate
        createtemplatejob = normalize_CreateTemplate(template_tier, source_tier, template_id, hierarchies, matrix, self.transferflag)
        self.files.update(createtemplatejob.files)
        CreateTemplate_Jobs.append(createtemplatejob)

        for ImageDim_Job in ImageDim_Jobs:
            dax.addJob(ImageDim_Job.pegasus_job)
        for CreateTemplate_Job in CreateTemplate_Jobs:
            dax.addJob(CreateTemplate_Job.pegasus_job)

        for CreateTemplate_Job in CreateTemplate_Jobs:
            for ImageDim_Job in ImageDim_Jobs:
                dax.depends(parent=ImageDim_Job.pegasus_job, child=CreateTemplate_Job.pegasus_job)

        #Possibly go deeper
        if len(hierarchies) > 2:
            child_matrix_set = matrix[hierarchies[1:]]
            for child_group, child_matrix in child_matrix_set.groupby(hierarchies[1]):
                dax, parents = self.__plan_tier__(child_matrix[hierarchies[1:]+["SPD"]], hierarchies[1:], dax)
                for parent in parents:
                    for ImageDim_Job in ImageDim_Jobs:
                        dax.depends(parent=parent.pegasus_job, child=ImageDim_Job.pegasus_job)

        #Will eventually return the last step in normalization for each tier
        return dax, CreateTemplate_Jobs



    def add_to_dax(self, dax):
        dax, parents = self.__plan_tier__(self.matrix, self.hierarchy, dax)
        self.parents = parents
        return dax

    def save_files(self, root):
        for filename, contents in self.files.iteritems():
            with open(root+"/"+filename, "w") as f:
                f.write(contents)

class normalize_ImageDim(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, hierarchy, matrix, transferflag):
        self.job_id = "{0}-{1}".format(source_tier, source_id)
        self.pegasus_job = Job(name="Normalize_ImageDim", namespace="dipa", id=self.job_id)
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputfile = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0]
        else:
            inputfile = "{0}-{1}_template.nii.gz".format(source_tier, source_id)
        outputfile = "{0}_dimensions.nii.gz".format(source_id)
        args = ["--id={0}".format(source_id), "--inputfile="+inputfile, "--outputfile="+outputfile]
        self.pegasus_job.uses(inputfile, link=Link.INPUT)
        self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)
        self.pegasus_job.addArguments(*args)

class normalize_CreateTemplate(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, transferflag):
        self.job_id = "{0}-{1}".format(template_tier, template_id)
        self.pegasus_job = Job(name="Normalize_CreateTemplate", namespace="dipa", id=self.job_id)
        self.files = {}


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
            spd_inputs = list(matrix[matrix[template_tier] == template_id]["SPD"])
        else:
            spd_inputs = []
            for source_id in source_ids:
                spd_inputs.append("{0}-{1}_template.nii.gz".format(source_tier, source_id))

        initial_template_input_text = "\n".join(spd_inputs)
        input_files.extend(spd_inputs)
        input_csv_contents = matrix[[source_tier]]
        files = input_csv_contents[source_tier].apply(lambda row: "{0}_dimensions.nii.gz".format(row))
        ids = input_csv_contents[source_tier]
        contents = pandas.DataFrame({"ID":ids, "FILE":files})
        input_csv_text = contents.to_csv(columns=["ID","FILE"], index=False)

        self.files["{0}_initial_template_input.txt".format(template_id)] = initial_template_input_text
        self.files["{0}_dimension_files.csv".format(template_id)] = input_csv_text
        for source_id in source_ids:
            input_files.append("{0}_dimensions.nii.gz".format(source_id))

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)
