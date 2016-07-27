#!/bin/python
from Pegasus.DAX3 import *
import os
import sys
import pandas

class normalize(object):
    """
    Normalize component of DIPA.
    Uses DTI-TK to normalize subjects to an iteratively improved template, or a predefined one.
    matrix is assumed to be a pandas dataframe. "hierarchy" is a list referencing headers in the matrix.
    """
    def __init__(self, matrix, hierarchy=["PROJECT", "ID"], name="Project", template=None, similarity_metric="NMI", species="Human", rigid=3, affine=3, diffeomorphic=6, transferflag=True):
        self.name = name
        self.matrix = matrix.copy()

        self.hierarchy = hierarchy
        if template != None:
            self.rigid = 1
            self.affine = 1
            self.diffeomorphic = 1
            #Override hierarchy in normalization. Register directly to the template.
            self.hierarchy = ["PROJECT", "ID"]
        else:
            self.rigid = rigid
            self.affine = affine
            self.diffeomorphic = diffeomorphic
            for setting in [self.rigid, self.affine, self.diffeomorphic]:
                if setting == 0:
                    setting = 1
            if "ID" not in self.hierarchy:
                self.hierarchy.append("ID")
            if "PROJECT" not in self.hierarchy:
                self.hierarchy = ["PROJECT"] + self.hierarchy

        #Rework the matrix file:
        self.matrix["SPD_NEW"] = matrix.apply(lambda row: self.__get_unique_matrix_key__(row)+"_spd.nii.gz", axis=1)

        self.mappings = pandas.DataFrame({"SOURCE":self.matrix["SPD"], "DESTINATION": self.matrix["SPD_NEW"]})
        self.matrix["SPD"] = self.matrix["SPD_NEW"]
        self.matrix.drop("SPD_NEW",1)


        if template == None:
            self.template = None
            self.resampled_template = None
        else:
            self.template = "{0}_template_orig.nii.gz".format(self.name)
            self.resampled_template = "{0}_template.nii.gz".format(self.name)

        self.similarity_metric = similarity_metric
        self.species = species.upper()
        self.files = {}
        self.transferflag = transferflag

        sep_lookup = {
        "HUMAN":"4",
        "MONKEY":"2",
        "RAT":"0.4"
        }
        try:
            self.sep_coarse = sep_lookup[self.species]
        except:
            print("The species you specified is not recognized. Select one of {0}".format(sep_lookup.keys()))
            sys.exit(1)


        if "PROJECT" not in self.matrix.columns:
            self.matrix["PROJECT"] = self.name
        try:
            self.matrix = self.matrix[self.hierarchy + ["SPD"]]
        except:
            print("The spreadsheet you supplied did not have columns for the hierarchy specified. Exiting.")
            sys.exit(1)

    def __get_unique_matrix_key__(self, row):
        values = []
        for level in self.hierarchy:
            if level != "PROJECT":
                values.append(str(row[level]))
        return "_".join(values)

    def __plan_tier__(self, matrix, hierarchies, dax):

        #Plan normalization here
        template_tier = hierarchies[0]
        template_id = matrix[hierarchies[0]].unique()[0]
        source_tier = hierarchies[1]
        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])

        #ImageDim
        ImageDim_Jobs = []
        for source_id in source_ids:
            imagedimjob = normalize_ImageDim(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, template=self.resampled_template, transferflag=self.transferflag)
            self.files.update(imagedimjob.files)
            ImageDim_Jobs.append(imagedimjob)
            dax.addJob(imagedimjob.pegasus_job)

        #CreateTemplate
        createtemplatejob = normalize_CreateTemplate(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, template=self.resampled_template, transferflag=self.transferflag)
        self.files.update(createtemplatejob.files)
        dax.addJob(createtemplatejob.pegasus_job)
        for ImageDim_Job in ImageDim_Jobs:
            dax.depends(parent=ImageDim_Job.pegasus_job, child=createtemplatejob.pegasus_job)

        #Rigid
        for rigid_iteration in range(1,self.rigid+1):
            RigidWarp_Jobs = []
            #Individual Warp
            for source_id in source_ids:
                rigidjob = normalize_RigidWarp(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, iteration=rigid_iteration, smoption=self.similarity_metric, sepcoarse=self.sep_coarse, template=self.template, transferflag=self.transferflag)
                self.files.update(rigidjob.files)
                RigidWarp_Jobs.append(rigidjob)
                dax.addJob(rigidjob.pegasus_job)
                dax.depends(parent=createtemplatejob.pegasus_job, child=rigidjob.pegasus_job)

            #Group Mean
            if self.template == None:
                rigidmeanjob=normalize_RigidMean(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, iteration=rigid_iteration, smoption=self.similarity_metric, transferflag=self.transferflag)
                dax.addJob(rigidmeanjob.pegasus_job)
                self.files.update(rigidmeanjob.files)
                for RigidWarp_Job in RigidWarp_Jobs:
                    dax.depends(parent=RigidWarp_Job.pegasus_job, child=rigidmeanjob.pegasus_job)

        #Affine
        for affine_iteration in range(1,self.affine+1):
            pass
        #Diffeomorphic
        for diffeo_iteration in range(1,self.diffeomorphic+1):
            pass

        #Possibly go deeper
        if len(hierarchies) > 2:
            child_matrix_set = matrix[hierarchies[1:]]
            for child_group, child_matrix in child_matrix_set.groupby(hierarchies[1]):
                dax, parents = self.__plan_tier__(child_matrix[hierarchies[1:]+["SPD"]], hierarchies[1:], dax)
                for parent in parents:
                    for ImageDim_Job in ImageDim_Jobs:
                        dax.depends(parent=parent.pegasus_job, child=ImageDim_Job.pegasus_job)

        #Will eventually return the last step in normalization for each tier
        if self.template == None:
            return dax, [rigidmeanjob]
        else:
            return dax, RigidWarp_Jobs



    def add_to_dax(self, dax):
        dax, parents = self.__plan_tier__(self.matrix, self.hierarchy, dax)
        self.parents = parents
        return dax

    def save_files(self, root):
        for filename, contents in self.files.iteritems():
            with open(root+"/"+filename, "w") as f:
                f.write(contents)

class normalize_ImageDim(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, hierarchy, matrix, transferflag, template=None):
        self.job_id = "{0}-{1}".format(source_tier, source_id)
        self.pegasus_job = Job(name="Normalize_ImageDim", namespace="dipa", id=self.job_id+"_Normalize_ImageDim")
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputfile = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0]
        else:
            inputfile = "{0}-{1}_template_orig.nii.gz".format(source_tier, source_id)
        if template == None:
            outputfile = "{0}_dimensions.csv".format(source_id)
            idval = source_id
        else:
            outputfile = "{0}_dimensions.csv".format(template_id)
            idval = template_id
        args = ["--id="+str(idval), "--inputfile="+inputfile, "--outputfile="+outputfile]

        self.pegasus_job.uses(inputfile, link=Link.INPUT)
        self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)
        self.pegasus_job.addArguments(*args)

class normalize_CreateTemplate(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, transferflag, template=None):
        self.job_id = "{0}-{1}".format(template_tier, template_id)
        self.pegasus_job = Job(name="Normalize_CreateTemplate", namespace="dipa", id=self.job_id+"_Normalize_CreateTemplate")
        self.files = {}

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])

        if template == None:
            args = ["--lookupfile", "{0}_dimension_files.csv".format(template_id),
                    "--templateinputsfile", "{0}_initial_template_input.txt".format(template_id),
                    "--resamplefile", "{0}_template_resample_bool.txt".format(template_id),
                    "--vsizefile", "{0}_template_vsize.txt".format(template_id),
                    "--isovsizefile", "{0}_template_iso_vsize.txt".format(template_id),
                    "--dimsizefile", "{0}_template_dim.txt".format(template_id),
                    "--orig", "{0}_initial_template_orig.nii.gz".format(template_id),
                    "--initial", "{0}_initial_template.nii.gz".format(template_id)]

            input_files = ["{0}_dimension_files.csv".format(template_id),
                           "{0}_initial_template_input.txt".format(template_id)]

            output_files = ["{0}_template_resample_bool.txt".format(template_id),
                            "{0}_template_vsize.txt".format(template_id),
                            "{0}_template_iso_vsize.txt".format(template_id),
                            "{0}_template_dim.txt".format(template_id),
                            "{0}_initial_template_orig.nii.gz".format(template_id),
                            "{0}_initial_template.nii.gz".format(template_id)]

        else:
            args = ["--lookupfile", "{0}_dimension_files.csv".format(template_id),
                    "--resamplefile", "{0}_template_resample_bool.txt".format(template_id),
                    "--vsizefile", "{0}_template_vsize.txt".format(template_id),
                    "--isovsizefile", "{0}_template_iso_vsize.txt".format(template_id),
                    "--dimsizefile", "{0}_template_dim.txt".format(template_id),
                    "--initial", "{0}_template.nii.gz".format(template_id),
                    "--srctemplate", "{0}_template_orig.nii.gz".format(template_id)]

            input_files = ["{0}_dimension_files.csv".format(template_id),
                           "{0}_template_orig.nii.gz".format(template_id)]

            output_files = ["{0}_template_resample_bool.txt".format(template_id),
                            "{0}_template_vsize.txt".format(template_id),
                            "{0}_template_iso_vsize.txt".format(template_id),
                            "{0}_template_dim.txt".format(template_id),
                            "{0}_template.nii.gz".format(template_id)]

        self.pegasus_job.addArguments(*args)

        if source_tier == "ID":
            spd_inputs = list(matrix[matrix[template_tier] == template_id]["SPD"])
        else:
            spd_inputs = []
            for source_id in source_ids:
                spd_inputs.append("{0}-{1}_template.nii.gz".format(source_tier, source_id))


        ##### !!! MODIFY FOR PREDEFINED TEMPLATES
        if template == None:
            initial_template_input_text = "\n".join(spd_inputs)
            input_files.extend(spd_inputs)
            input_csv_contents = matrix[[source_tier]]
            files = input_csv_contents[source_tier].apply(lambda row: "{0}_dimensions.csv".format(row))
            ids = input_csv_contents[source_tier]
            contents = pandas.DataFrame({"ID":ids, "FILE":files})
            input_csv_text = contents.to_csv(columns=["ID","FILE"], index=False)

            self.files["{0}_initial_template_input.txt".format(template_id)] = initial_template_input_text
            self.files["{0}_dimension_files.csv".format(template_id)] = input_csv_text
            for source_id in source_ids:
                input_files.append("{0}_dimensions.csv".format(source_id))

        else:
            self.files["{0}_dimension_files.csv".format(template_id)] = "ID,FILE\n{0},{0}_dimensions.csv".format(template_id)

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_RigidWarp(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, iteration, smoption, sepcoarse, hierarchy, matrix, transferflag, template=None):
        self.job_id = "{0}-{1}_i{2}".format(source_tier, source_id, iteration)
        self.pegasus_job = Job(name="Normalize_RigidWarp", namespace="dipa", id=self.job_id+"_Normalize_RigidWarp")
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputfile = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0]
        else:
            inputfile = "{0}-{1}_template.nii.gz".format(source_tier, source_id)

        inputbase = inputfile.split(".")[0]
        if iteration == 1 and template == None:
            template_image = "{0}_initial_template.nii.gz".format(template_id)
        elif template != None:
            template_image = "{0}_template.nii.gz".format(template_id)
        else:
            template_image = "{0}_mean_rigid{1}.nii.gz".format(template_id, iteration-1)

        inputfiles = [inputfile, template_image]
        outputfiles = ["{0}_ri{1}_aff.nii.gz".format(inputbase, iteration), "{0}_ri{1}.aff".format(inputbase, iteration)]
        args = ["--mean", template_image,
                "--image", inputfile,
                "--outimage", "{0}_ri{1}_aff.nii.gz".format(inputbase, iteration),
                "--outaff", "{0}_ri{1}.aff".format(inputbase, iteration),
                "--smoption", smoption,
                "--sepcoarse", sepcoarse]
        if iteration == 1:
            args.append("--initial")

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_RigidMean(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, iteration, smoption, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(template_tier, template_id, iteration)
        self.pegasus_job = Job(name="Normalize_RigidMean", namespace="dipa", id=self.job_id+"_Normalize_RigidMean")
        self.files = {}

        args = ["--affinelist", "{0}_rigid_i{1}_template_input.txt".format(template_id, iteration),
                "--newmean", "{0}_mean_rigid{1}.nii.gz".format(template_id, iteration),
                "--smoption", smoption]

        self.pegasus_job.addArguments(*args)

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])

        aff_files = []
        for source_id in source_ids:
            if source_tier == hierarchy[-1]:
                inputfile_base = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]

            else:
                inputfile_base = "{0}-{1}_template".format(source_tier, source_id)
            aff_files.append(inputfile_base + "_ri{0}_aff.nii.gz".format(iteration))

        input_files = ["{0}_rigid_i{1}_template_input.txt".format(template_id, iteration)] + aff_files

        output_files = ["{0}_mean_rigid{1}.nii.gz".format(template_id, iteration)]

        rigid_template_input_text = "\n".join(aff_files)

        self.files["{0}_rigid_i{1}_template_input.txt".format(template_id, iteration)] = rigid_template_input_text

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_AffineWarpA(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, iteration, smoption, sepcoarse, hierarchy, matrix, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(source_tier, source_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineWarpA", namespace="dipa", id=self.job_id+"_Normalize_AffineWarpA")
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputfile = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0]
        else:
            inputfile = "{0}-{1}_template.nii.gz".format(source_tier, source_id)

        inputbase = inputfile.split(".")[0]
        if iteration == 1:
            template_image = "{0}_initial_template.nii.gz".format(template_id)
        else:
            template_image = "{0}_mean_rigid{1}.nii.gz".format(template_id, iteration-1)

        inputfiles = [inputfile, template_image]
        outputfiles = ["{0}_aff.nii.gz".format(inputbase), "{0}.aff".format(inputbase)]
        args = ["--mean", template_image,
                "--image", inputfile,
                "--outimage", "{0}_ai{1}_aff.nii.gz".format(inputbase, iteration),
                "--outaff", "{0}_ai{1}.aff".format(inputbase, iteration),
                "--smoption", smoption,
                "--sepcoarse", sepcoarse]
        if iteration == 1:
            args.append("--initial")

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_AffineMeanA(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, iteration, smoption, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(template_tier, template_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineMeanA", namespace="dipa", id=self.job_id+"_Normalize_AffineMeanA")
        self.files = {}

        args = ["--invlist", "{0}_inv_template_input.txt".format(template_id),
                "--invmean", "{0}_mean_inv{1}.nii.gz".format(template_id, iteration),
                "--invaff", "{0}_mean_inv{1}.aff".format(template_id, iteration)]

        self.pegasus_job.addArguments(*args)

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])

        aff_files = []
        for source_id in source_ids:
            if source_tier == hierarchy[-1]:
                inputfile_base = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
            else:
                inputfile_base = "{0}-{1}_template".format(source_tier, source_id)
            aff_files.append(inputfile_base + ".aff")

        input_files = ["{0}_inv_template_input.txt".format(template_id)] + aff_files

        output_files = ["{0}_mean_inv{1}.nii.gz".format(template_id, iteration),
                        "{0}_mean_inv{1}.aff".format(template_id, iteration)]

        inv_template_input_text = "\n".join(aff_files)

        self.files["{0}_inv_template_input.txt".format(template_id)] = inv_template_input_text

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_AffineWarpB(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, iteration, smoption, sepcoarse, rigid_iteratons, hierarchy, matrix, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(source_tier, source_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineWarpB", namespace="dipa", id=self.job_id+"_Normalize_AffineWarpB")
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputfile = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0]
        else:
            inputfile = "{0}-{1}_template.nii.gz".format(source_tier, source_id)

        inputbase = inputfile.split(".")[0]
        if iteration == 1:
            template_image = "{0}_mean_rigid{1}.nii.gz".format(template_id, rigid_iterations)
        else:
            template_image = "{0}_mean_affine{1}.nii.gz".format(template_id, iteration-1)

        Input = ["{0}/Data/${{ID}}/Fit/DTI/${{ID}}_spd.nii.gz".format(config["ScriptSettings"]["DataDir"]),
                   "{0}/Data/${{ID}}/Normalize/${{ID}}_spd.aff".format(config["ScriptSettings"]["DataDir"]),
                   "{0}/Data/${{ID}}/Normalize/${{ID}}_spd_aff.nii.gz".format(config["ScriptSettings"]["DataDir"]),
                   "{0}/Data/Project/Normalize/mean_affine{1}.nii.gz".format(config["ScriptSettings"]["DataDir"], iteration-1),
                   "{0}/Data/Project/Normalize/mean_inv{1}.aff".format(config["ScriptSettings"]["DataDir"], iteration)],
        Output = ["{0}/Data/${{ID}}/Normalize/${{ID}}_spd_aff.nii.gz".format(config["ScriptSettings"]["DataDir"]),
                  "{0}/Data/${{ID}}/Normalize/${{ID}}_spd.aff".format(config["ScriptSettings"]["DataDir"])],


        inputfiles = [inputfile, "{0}.aff".format(inputbase), "{0}_aff.nii.gz".format(inputbase), template_image, "{0}_mean_inv{1}.aff".format(template_id, iteration)]
        outputfiles = ["{0}_aff.nii.gz".format(inputbase), "{0}.aff".format(inputbase)]
        args = ["--mean", template_image,
                "--image", inputfile,
                "--smoption", smoption,
                "--sepcoarse", sepcoarse]
        if iteration == 1:
            args.append("--initial")

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_AffineMeanB(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, iteration, smoption, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(template_tier, template_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineMeanB", namespace="dipa", id=self.job_id+"_Normalize_AffineMeanB")
        self.files = {}

        args = ["--invlist", "{0}_inv_template_input.txt".format(template_id),
                "--invmean", "{0}_mean_inv{1}.nii.gz".format(template_id, iteration),
                "--invaff", "{0}_mean_inv{1}.aff".format(template_id, iteration)]

        self.pegasus_job.addArguments(*args)

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier])

        aff_files = []
        for source_id in source_ids:
            if source_tier == hierarchy[-1]:
                inputfile_base = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
                aff_files.append(inputfile_base + ".aff")
            else:
                aff_files.append("{0}-{1}_template.aff".format(source_tier, source_id))

        input_files = ["{0}_inv_template_input.txt".format(template_id)] + aff_files

        output_files = ["{0}_mean_inv{1}.nii.gz".format(template_id, iteration),
                        "{0}_mean_inv{1}.aff".format(template_id, iteration)]

        inv_template_input_text = "\n".join(aff_files)

        self.files["{0}_inv_template_input.txt".format(template_id)] = inv_template_input_text

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)
