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
            self.rigid = int(rigid)
            self.affine = int(affine)
            self.diffeomorphic = int(diffeomorphic)
            if self.rigid < 1:
                self.rigid = 1
            if self.affine < 1:
                self.affine = 1
            if self.diffeomorphic < 1:
                self.diffeomorphic = 1
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
        "HUMAN":"4.0",
        "MONKEY":"2.0",
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

        self.initial_steps = []
        self.final_steps = []

    def __get_unique_matrix_key__(self, row):
        values = []
        for level in self.hierarchy:
            if level != "PROJECT":
                values.append(str(row[level]))
        return "_".join(values)

    def __plan_tier__(self, matrix, hierarchies, dax, initial=True):

        #Plan normalization here
        template_tier = hierarchies[0]
        template_id = matrix[hierarchies[0]].unique()[0]
        source_tier = hierarchies[1]
        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())

        #ImageDim
        ImageDim_Jobs = []
        for source_id in source_ids:
            imagedimjob = normalize_ImageDim(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, template=self.resampled_template, transferflag=self.transferflag)
            self.files.update(imagedimjob.files)
            ImageDim_Jobs.append(imagedimjob)
            dax.addJob(imagedimjob.pegasus_job)
            if source_tier == hierarchies[-1]:
                #Base Tier, add to self.initial_steps
                self.initial_steps.append(imagedimjob)

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
                rigidjob = normalize_RigidWarp(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, iteration=rigid_iteration, smoption=self.similarity_metric, sepcoarse=self.sep_coarse, template=self.resampled_template, transferflag=self.transferflag)
                self.files.update(rigidjob.files)
                RigidWarp_Jobs.append(rigidjob)
                dax.addJob(rigidjob.pegasus_job)
                if rigid_iteration == 1:
                    dax.depends(parent=createtemplatejob.pegasus_job, child=rigidjob.pegasus_job)
                else:
                    dax.depends(parent=rigidmeanjob.pegasus_job, child=rigidjob.pegasus_job)

            #Group Mean
            if self.template == None:
                rigidmeanjob=normalize_RigidMean(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, iteration=rigid_iteration, smoption=self.similarity_metric, transferflag=self.transferflag)
                dax.addJob(rigidmeanjob.pegasus_job)
                self.files.update(rigidmeanjob.files)
                for RigidWarp_Job in RigidWarp_Jobs:
                    dax.depends(parent=RigidWarp_Job.pegasus_job, child=rigidmeanjob.pegasus_job)

        #Affine
        for affine_iteration in range(1,self.affine+1):
            AffineWarpA_Jobs = []
            AffineWarpB_Jobs = []
            #Individual Warp, Part A
            for index, source_id in enumerate(source_ids):
                affinewarpajob = normalize_AffineWarpA(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, iteration=affine_iteration, template=self.resampled_template, smoption=self.similarity_metric, rigid=self.rigid, sepcoarse=self.sep_coarse, transferflag=self.transferflag)
                AffineWarpA_Jobs.append(affinewarpajob)
                dax.addJob(affinewarpajob.pegasus_job)
                self.files.update(affinewarpajob.files)
                if affine_iteration == 1:
                    if self.template == None:
                        dax.depends(parent=rigidmeanjob.pegasus_job, child=affinewarpajob.pegasus_job)
                    else:
                        dax.depends(parent=RigidWarp_Jobs[index].pegasus_job, child=affinewarpajob.pegasus_job)
                else:
                    dax.depends(parent=affinemeanbjob.pegasus_job, child=affinewarpajob.pegasus_job)

            #Group Mean, Part A
            affinemeanajob = normalize_AffineMeanA(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, iteration=affine_iteration, smoption=self.similarity_metric, template=self.resampled_template, rigid=self.rigid, transferflag=self.transferflag)
            dax.addJob(affinemeanajob.pegasus_job)
            self.files.update(affinemeanajob.files)
            for AffineWarpA_Job in AffineWarpA_Jobs:
                dax.depends(parent=AffineWarpA_Job.pegasus_job, child=affinemeanajob.pegasus_job)

            #Individual Warp, Part B
            for source_id in source_ids:
                affinewarpbjob = normalize_AffineWarpB(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, iteration=affine_iteration, smoption=self.similarity_metric, sepcoarse=self.sep_coarse, template=self.resampled_template, rigid=self.rigid, transferflag=self.transferflag)
                AffineWarpB_Jobs.append(affinewarpbjob)
                dax.addJob(affinewarpbjob.pegasus_job)
                self.files.update(affinewarpbjob.files)
                dax.depends(parent=affinemeanajob.pegasus_job, child=affinewarpbjob.pegasus_job)

            #Group Mean, Part B
            affinemeanbjob = normalize_AffineMeanB(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, iteration=affine_iteration, smoption=self.similarity_metric, template=self.resampled_template, transferflag=self.transferflag)
            dax.addJob(affinemeanbjob.pegasus_job)
            self.files.update(affinemeanbjob.files)
            for AffineWarpB_Job in AffineWarpB_Jobs:
                dax.depends(parent=AffineWarpB_Job.pegasus_job, child=affinemeanbjob.pegasus_job)

        #Diffeomorphic
        for diffeo_iteration in range(1,self.diffeomorphic+1):
            DiffeoWarp_Jobs = []
            #Individual Warp
            for source_id in source_ids:
                diffeowarpjob = normalize_DiffeomorphicWarp(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, iteration=diffeo_iteration, template=self.resampled_template, affine=self.affine, transferflag=self.transferflag)
                dax.addJob(diffeowarpjob.pegasus_job)
                DiffeoWarp_Jobs.append(diffeowarpjob)
                self.files.update(diffeowarpjob.files)
                if diffeo_iteration == 1:
                    dax.depends(parent=affinemeanbjob.pegasus_job, child=diffeowarpjob.pegasus_job)
                else:
                    dax.depends(parent=diffeomeanjob.pegasus_job, child=diffeowarpjob.pegasus_job)

            #Group Mean
            if self.template == None:
                diffeomeanjob = normalize_DiffeomorphicMean(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, iteration=diffeo_iteration, transferflag=self.transferflag)
                dax.addJob(diffeomeanjob.pegasus_job)
                self.files.update(diffeomeanjob.files)
                for DiffeoWarp_Job in DiffeoWarp_Jobs:
                    dax.depends(parent=DiffeoWarp_Job.pegasus_job, child=diffeomeanjob.pegasus_job)

        #Composition
        ComposeWarp_Jobs = []
        for index, source_id in enumerate(source_ids):
            composewarpjob = normalize_ComposeWarp(template_tier=template_tier, source_tier=source_tier, template_id=template_id, source_id=source_id, hierarchy=hierarchies, matrix=matrix, template=self.resampled_template, affine=self.affine, diffeomorphic=self.diffeomorphic, transferflag=self.transferflag)
            dax.addJob(composewarpjob.pegasus_job)
            ComposeWarp_Jobs.append(composewarpjob)
            self.files.update(composewarpjob.files)
            if self.template == None:
                dax.depends(parent=diffeomeanjob.pegasus_job, child=composewarpjob.pegasus_job)
            else:
                dax.depends(parent=DiffeoWarp_Jobs[index].pegasus_job, child=composewarpjob.pegasus_job)

        composemeanjob = normalize_ComposeMean(template_tier=template_tier, source_tier=source_tier, template_id=template_id, hierarchy=hierarchies, matrix=matrix, template=self.resampled_template, transferflag=self.transferflag)
        dax.addJob(composemeanjob.pegasus_job)
        self.files.update(composemeanjob.files)
        for ComposeWarp_Job in ComposeWarp_Jobs:
            dax.depends(parent=ComposeWarp_Job.pegasus_job, child=composemeanjob.pegasus_job)

        #Possibly go deeper
        if len(hierarchies) > 2:
            child_matrix_set = matrix[hierarchies[1:]+["SPD"]]
            for child_group, child_matrix in child_matrix_set.groupby(hierarchies[1]):
                dax, parents = self.__plan_tier__(child_matrix[hierarchies[1:]+["SPD"]], hierarchies[1:], dax, initial=False)
                for parent in parents:
                    for ImageDim_Job in ImageDim_Jobs:
                        dax.depends(parent=parent.pegasus_job, child=ImageDim_Job.pegasus_job)


        if initial == True and len(hierarchies) > 2:
            #Run CreateFullComposedWarp to generate the Bottom->Top warp across hierarchies
            ComposeFullWarp_Jobs = []
            child_matrix_set = matrix[hierarchies+["SPD"]]
            for child_index, child_matrix in child_matrix_set.groupby(hierarchies):
                composefullwarpjob = normalize_ComposeFullWarp(child_index, child_matrix, hierarchies, self.transferflag)
                self.files.update(composefullwarpjob.files)
                ComposeFullWarp_Jobs.append(composefullwarpjob)
                dax.addJob(composefullwarpjob.pegasus_job)
                dax.depends(parent=composemeanjob.pegasus_job, child=composefullwarpjob.pegasus_job)
            self.final_steps = ComposeFullWarp_Jobs
            return dax, ComposeFullWarp_Jobs
        else:
            #Return the last step in normalization for each tier (ComposeMean)
            if initial == True:
                self.final_steps = [composemeanjob]
            return dax, [composemeanjob]



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
            inputfile = "{0}-{1}_template.nii.gz".format(source_tier, source_id)
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

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())

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

        if template == None:
            initial_template_input_text = "\n".join(spd_inputs)+"\n"
            input_files.extend(spd_inputs)
            input_csv_contents = matrix[[source_tier]]
            files = input_csv_contents[source_tier].apply(lambda row: "{0}_dimensions.csv".format(row))
            ids = input_csv_contents[source_tier]
            contents = pandas.DataFrame({"ID":ids, "FILE":files}).drop_duplicates()
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
        sep=sepcoarse
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

        if iteration != 1:
            aff_input_files = [inputbase+"_ri{0}.aff".format(iteration-1)]
        else:
            aff_input_files = []

        inputfiles = [inputfile, template_image] + aff_input_files
        outputfiles = ["{0}_ri{1}_aff.nii.gz".format(inputbase, iteration), "{0}_ri{1}.aff".format(inputbase, iteration)]
        args = ["--mean", template_image,
                "--image", inputfile,
                "--outimage", "{0}_ri{1}_aff.nii.gz".format(inputbase, iteration),
                "--outaff", "{0}_ri{1}.aff".format(inputbase, iteration),
                "--smoption", smoption,
                "--sep", sep]
        if iteration == 1:
            args.extend(["--initial","True"])
        else:
            args.extend(["--aff",inputbase+"_ri{0}.aff".format(iteration-1)])

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

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())

        aff_image_files = []
        for source_id in source_ids:
            if source_tier == hierarchy[-1]:
                inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]

            else:
                inputbase = "{0}-{1}_template".format(source_tier, source_id)
            aff_image_files.append(inputbase + "_ri{0}_aff.nii.gz".format(iteration))


        input_files = ["{0}_rigid_i{1}_template_input.txt".format(template_id, iteration)] + aff_image_files

        output_files = ["{0}_mean_rigid{1}.nii.gz".format(template_id, iteration)]

        rigid_template_input_text = "\n".join(aff_image_files)+"\n"

        self.files["{0}_rigid_i{1}_template_input.txt".format(template_id, iteration)] = rigid_template_input_text

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_AffineWarpA(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, iteration, smoption, sepcoarse, hierarchy, matrix, template, rigid, transferflag):
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
            template_image = "{0}_mean_rigid{1}.nii.gz".format(template_id, rigid)
            previous_iter = ["{0}_ri{1}_aff.nii.gz".format(inputbase, rigid),
                             "{0}_ri{1}.aff".format(inputbase, rigid)]
        else:
            template_image = "{0}_mean_affine{1}.nii.gz".format(template_id, iteration-1)
            previous_iter = ["{0}_ai{1}b_aff.nii.gz".format(inputbase, iteration-1),
                             "{0}_ai{1}b.aff".format(inputbase, iteration-1)]

        if template != None:
            template_image = "{0}_template.nii.gz".format(template_id)

        inputfiles = [inputfile, template_image] + previous_iter
        outputfiles = ["{0}_ai{1}a_aff.nii.gz".format(inputbase, iteration),
                       "{0}_ai{1}a.aff".format(inputbase, iteration)]

        args = ["--mean", template_image,
                "--image", inputfile,
                "--aff", previous_iter[1],
                "--outimage", "{0}_ai{1}a_aff.nii.gz".format(inputbase, iteration),
                "--outaff", "{0}_ai{1}a.aff".format(inputbase, iteration),
                "--smoption", smoption,
                "--sepcoarse", sepcoarse]

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_AffineMeanA(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, iteration, rigid, smoption, template, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(template_tier, template_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineMeanA", namespace="dipa", id=self.job_id+"_Normalize_AffineMeanA")
        self.files = {}

        if iteration == 1:
            template_image = "{0}_mean_rigid{1}.nii.gz".format(template_id, rigid)
        else:
            template_image = "{0}_mean_affine{1}.nii.gz".format(template_id, iteration-1)

        if template != None:
            template_image = "{0}_template.nii.gz".format(template_id)

        args = ["--invlist", "{0}_inv_affine_i{1}_input.txt".format(template_id, iteration),
                "--mean", template_image,
                "--invaff", "{0}_inv{1}.aff".format(template_id, iteration)]

        self.pegasus_job.addArguments(*args)

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())

        aff_files = []
        for source_id in source_ids:
            if source_tier == hierarchy[-1]:
                inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
            else:
                inputbase = "{0}-{1}_template".format(source_tier, source_id)
            aff_files.append(inputbase + "_ai{0}a.aff".format(iteration))

        input_files = ["{0}_inv_affine_i{1}_input.txt".format(template_id, iteration)] + aff_files

        output_files = ["{0}_inv{1}.aff".format(template_id, iteration)]

        inv_template_input_text = "\n".join(aff_files)+"\n"

        self.files["{0}_inv_affine_i{1}_input.txt".format(template_id, iteration)] = inv_template_input_text

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_AffineWarpB(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, iteration, smoption, template, sepcoarse, rigid, hierarchy, matrix, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(source_tier, source_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineWarpB", namespace="dipa", id=self.job_id+"_Normalize_AffineWarpB")
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
        else:
            inputbase = "{0}-{1}_template".format(source_tier, source_id)
        inputfile = inputbase+".nii.gz"

        if template == None:
            if iteration == 1:
                template_image = "{0}_mean_rigid{1}.nii.gz".format(template_id, rigid)
            else:
                template_image = "{0}_mean_affine{1}.nii.gz".format(template_id, iteration-1)
        else:
            template_image = "{0}_template.nii.gz".format(template_id)



        inputfiles = [inputfile, template_image, "{0}_inv{1}.aff".format(template_id, iteration), inputbase+"_ai{0}a.aff".format(iteration)]
        outputfiles = ["{0}_ai{1}b_aff.nii.gz".format(inputbase, iteration),
                       "{0}_ai{1}b.aff".format(inputbase, iteration)]

        args = ["--mean", template_image,
                "--invmean", "{0}_inv{1}.aff".format(template_id, iteration),
                "--image", inputfile,
                "--smoption", smoption,
                "--sepcoarse", sepcoarse,
                "--inaff", inputbase+"_ai{0}a.aff".format(iteration),
                "--outaffimage", "{0}_ai{1}b_aff.nii.gz".format(inputbase, iteration),
                "--outaff", "{0}_ai{1}b.aff".format(inputbase, iteration)]

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_AffineMeanB(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, iteration, smoption, template, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(template_tier, template_id, iteration)
        self.pegasus_job = Job(name="Normalize_AffineMeanB", namespace="dipa", id=self.job_id+"_Normalize_AffineMeanB")
        self.files = {}

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())

        aff_files = []
        if template == None:
            for source_id in source_ids:
                if source_tier == hierarchy[-1]:
                    inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
                else:
                    inputbase = "{0}-{1}_template".format(source_tier, source_id)
                aff_files.append(inputbase + "_ai{0}b_aff.nii.gz".format(iteration))

            aff_template_input_text = "\n".join(aff_files)+"\n"
            self.files["{0}_affine_i{1}_template_input.txt".format(template_id, iteration)] = aff_template_input_text

        if template == None:
            args = ["--affinelist", "{0}_affine_i{1}_template_input.txt".format(template_id, iteration),
                    "--mean", "{0}_mean_affine{1}.nii.gz".format(template_id, iteration),
                    "--trace", "{0}_mean_affine{1}_tr.nii.gz".format(template_id, iteration),
                    "--mask", "{0}_mean_affine{1}_mask.nii.gz".format(template_id, iteration)]
            input_files = ["{0}_affine_i{1}_template_input.txt".format(template_id, iteration)] + aff_files
            output_files = ["{0}_mean_affine{1}.nii.gz".format(template_id, iteration),
                            "{0}_mean_affine{1}_tr.nii.gz".format(template_id, iteration),
                            "{0}_mean_affine{1}_mask.nii.gz".format(template_id, iteration)]
        else:
            args = ["--mean", "{0}_template.nii.gz".format(template_id),
                    "--trace", "{0}_template_tr.nii.gz".format(template_id, iteration),
                    "--mask", "{0}_template_mask.nii.gz".format(template_id, iteration),
                    "--staticmean", "True"]
            input_files = ["{0}_template.nii.gz".format(template_id)]
            output_files = ["{0}_template_tr.nii.gz".format(template_id, iteration), "{0}_template_mask.nii.gz".format(template_id, iteration)]

        self.pegasus_job.addArguments(*args)

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_DiffeomorphicWarp(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, iteration, affine, hierarchy, matrix, transferflag, template=None):
        self.job_id = "{0}-{1}_i{2}".format(source_tier, source_id, iteration)
        self.pegasus_job = Job(name="Normalize_DiffeomorphicWarp", namespace="dipa", id=self.job_id+"_Normalize_DiffeomorphicWarp")
        self.files = {}
        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
        else:
            inputbase = "{0}-{1}_template".format(source_tier, source_id)
        inputfile = inputbase+"_ai{0}b_aff.nii.gz".format(affine)

        if iteration == 1 and template == None:
            template_image = "{0}_mean_affine{1}.nii.gz".format(template_id, affine)
            template_mask_image = "{0}_mean_affine{1}_mask.nii.gz".format(template_id, affine)
        elif template != None:
            template_image = "{0}_template.nii.gz".format(template_id)
            template_mask_image = "{0}_template_mask.nii.gz".format(template_id)
        else:
            template_image = "{0}_mean_diffeomorphic{1}.nii.gz".format(template_id, iteration-1)
            template_mask_image = "{0}_mean_affine{1}_mask.nii.gz".format(template_id, affine)

        inputfiles = [inputfile, template_image]
        out_image = "{0}_di{1}.nii.gz".format(inputbase, iteration)
        out_df = "{0}_di{1}.df.nii.gz".format(inputbase, iteration)
        outputfiles = [out_image, out_df]
        args = ["--mean", template_image,
                "--image", inputfile,
                "--mask", template_mask_image,
                "--outimage", out_image,
                "--outdf", out_df,
                "--iterations", str(iteration)]

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_DiffeomorphicMean(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, iteration, transferflag):
        self.job_id = "{0}-{1}_i{2}".format(template_tier, template_id, iteration)
        self.pegasus_job = Job(name="Normalize_DiffeomorphicMean", namespace="dipa", id=self.job_id+"_Normalize_DiffeomorphicMean")
        self.files = {}

        template_image = "{0}_mean_diffeomorphic{1}.nii.gz".format(template_id, iteration)
        df_image = "{0}_mean_df{1}.nii.gz".format(template_id, iteration)
        invdf_image = "{0}_inv_df{1}.nii.gz".format(template_id, iteration)


        diffeo_input_list_file = "{0}_diffeomorphic_i{1}_template_input.txt".format(template_id, iteration)
        df_input_list_file = "{0}_diffeomorphic_i{1}_df_input.txt".format(template_id, iteration)

        args = ["--diffeolist", diffeo_input_list_file,
                "--dflist", df_input_list_file,
                "--mean", template_image,
                "--dfmean", df_image,
                "--invdfmean", invdf_image]

        self.pegasus_job.addArguments(*args)

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())

        diffeo_files = []
        df_files = []
        for source_id in source_ids:
            if source_tier == hierarchy[-1]:
                inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]

            else:
                inputbase = "{0}-{1}_template".format(source_tier, source_id)
            diffeo_files.append("{0}_di{1}.nii.gz".format(inputbase, iteration))
            df_files.append("{0}_di{1}.df.nii.gz".format(inputbase, iteration))

        input_files = [diffeo_input_list_file, df_input_list_file] + diffeo_files + df_files

        output_files = [template_image, df_image, invdf_image]

        diffeo_input_text = "\n".join(diffeo_files)+"\n"
        df_input_text = "\n".join(df_files)+"\n"

        self.files[diffeo_input_list_file] = diffeo_input_text
        self.files[df_input_list_file] = df_input_text

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_ComposeWarp(object):
    def __init__(self, template_tier, source_tier, template_id, source_id, affine, diffeomorphic, hierarchy, matrix, transferflag, template=None):
        self.job_id = "{0}-{1}".format(source_tier, source_id)
        self.pegasus_job = Job(name="Normalize_ComposeWarp", namespace="dipa", id=self.job_id+"_Normalize_ComposeWarp")
        self.files = {}

        composed_file = "{0}-{1}_{2}-{3}_composed.df.nii.gz".format(template_tier, template_id, source_tier, source_id)
        invcomposed_file = "{0}-{1}_{2}-{3}_composed_inv.df.nii.gz".format(template_tier, template_id, source_tier, source_id)
        warped_file = "{0}-{1}_{2}-{3}_composed.nii.gz".format(template_tier, template_id, source_tier, source_id)
        isowarped_file = "{0}-{1}_{2}-{3}_composed_iso.nii.gz".format(template_tier, template_id, source_tier, source_id)

        #Check to see if this is the basic level of the normalization.
        #If so, use the SPD specified. Otherwise, input is the output of a previous step.
        if source_tier == hierarchy[-1]:
            inputbase = list(matrix[matrix[template_tier] == template_id][matrix[source_tier] == source_id]["SPD"])[0].split(".")[0]
        else:
            inputbase = "{0}-{1}_template".format(source_tier, source_id)
        imagefile = inputbase+".nii.gz"
        aff_file = inputbase+"_ai{0}b.aff".format(affine)
        df_file = inputbase+"_di{0}.df.nii.gz".format(diffeomorphic)

        if template != None:
            template_image = "{0}_template.nii.gz".format(template_id)
        else:
            template_image = "{0}_mean_diffeomorphic{1}.nii.gz".format(template_id, diffeomorphic)

        iso_vsize_file = "{0}_template_iso_vsize.txt".format(template_id)

        inputfiles = [imagefile, template_image, aff_file, df_file, iso_vsize_file]
        outputfiles = [composed_file, invcomposed_file, warped_file, isowarped_file]
        args = ["--image", imagefile,
                "--mean", template_image,
                "--aff", aff_file,
                "--df", df_file,
                "--isovsize", iso_vsize_file,
                "--warped", warped_file,
                "--isowarped",isowarped_file,
                "--warp", composed_file,
                "--invwarp",invcomposed_file]

        for inputfile in inputfiles:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in outputfiles:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)

class normalize_ComposeMean(object):
    def __init__(self, template_tier, source_tier, template_id, hierarchy, matrix, template, transferflag):
        self.job_id = "{0}-{1}".format(template_tier, template_id)
        self.pegasus_job = Job(name="Normalize_ComposeMean", namespace="dipa", id=self.job_id+"_Normalize_ComposeMean")
        self.files = {}

        final_mean_file = "{0}-{1}_template.nii.gz".format(template_tier, template_id)
        final_isomean_file = "{0}-{1}_template_iso.nii.gz".format(template_tier, template_id)
        fa_final_mean_file = "{0}-{1}_template_fa.nii.gz".format(template_tier, template_id)
        fa_final_isomean_file = "{0}-{1}_template_iso_fa.nii.gz".format(template_tier, template_id)

        if template == None:
            compose_input_list_file = "{0}_compose_template_input.txt".format(template_id)
            compose_iso_input_list_file = "{0}_compose_iso_template_input.txt".format(template_id)
            args = [
                "--inputlist", compose_input_list_file,
                "--finalmean", final_mean_file,
                "--fafinalmean", fa_final_mean_file,
                "--isoinputlist", compose_iso_input_list_file,
                "--isofinalmean", final_isomean_file,
                "--isofafinalmean", fa_final_isomean_file
                ]
            input_files = [compose_input_list_file, compose_iso_input_list_file]
        else:
            iso_vsize_file = "{0}_template_iso_vsize.txt".format(template_id)
            dim_file = "{0}_template_dim.txt".format(template_id)
            args = [
                "--finalmean", final_mean_file,
                "--fafinalmean", fa_final_mean_file,
                "--isofinalmean", final_isomean_file,
                "--isofafinalmean", fa_final_isomean_file,
                "--origmean", template,
                "--isovsizefile", iso_vsize_file,
                "--dimsizefile", dim_file,
                "--statictemplate", "True"
                ]
            input_files = [template, iso_vsize_file, dim_file]
        output_files = [final_mean_file, fa_final_mean_file, final_isomean_file, fa_final_isomean_file]

        self.pegasus_job.addArguments(*args)

        source_ids = list(matrix[matrix[template_tier] == template_id][source_tier].unique())
        if template == None:
            input_image_files = []
            input_iso_image_files = []
            for source_id in source_ids:
                input_image_files.append("{0}-{1}_{2}-{3}_composed.nii.gz".format(template_tier, template_id, source_tier, source_id))
                input_iso_image_files.append("{0}-{1}_{2}-{3}_composed_iso.nii.gz".format(template_tier, template_id, source_tier, source_id))
            input_files.extend(input_image_files + input_iso_image_files)
            self.files[compose_input_list_file] = "\n".join(input_image_files)+"\n"
            self.files[compose_iso_input_list_file] = "\n".join(input_iso_image_files)+"\n"


        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

class normalize_ComposeFullWarp(object):
    def __init__(self, child_index, child_matrix, hierarchies, transferflag):
        self.job_id = "{0}-{1}".format(hierarchies[-1], child_index[-1])
        self.pegasus_job = Job(name="Normalize_ComposeFullWarp", namespace="dipa", id=self.job_id+"_Normalize_ComposeFullWarp")
        self.files = {}
        template_tier = hierarchies[0]
        template_id = child_index[0]
        source_tier = hierarchies[-1]
        source_id = child_index[-1]

        source_file = list(child_matrix["SPD"])[0]
        template_file = "{0}-{1}_template.nii.gz".format(template_tier, template_id)
        iso_vsize_file = "{0}_template_iso_vsize.txt".format(template_id)
        warped_file = "{0}-{1}_{2}-{3}_composed.nii.gz".format(template_tier, template_id, source_tier, source_id)
        isowarped_file = "{0}-{1}_{2}-{3}_composed_iso.nii.gz".format(template_tier, template_id, source_tier, source_id)
        out_warp_file = "{0}-{1}_{2}-{3}_composed.df.nii.gz".format(template_tier, template_id, source_tier, source_id)
        out_invwarp_file = "{0}-{1}_{2}-{3}_composed_inv.df.nii.gz".format(template_tier, template_id, source_tier, source_id)

        warp_files = []
        invwarp_files = []

        pairings = []
        for i in range(0,len(hierarchies)):
            pairings.append({"tier": hierarchies[i], "id":child_index[i]})
        for template, source in zip(pairings, pairings[1:]):
            warp_files.append("{0}-{1}_{2}-{3}_composed.df.nii.gz".format(template["tier"], template["id"], source["tier"], source["id"]))
            invwarp_files.append("{0}-{1}_{2}-{3}_composed_inv.df.nii.gz".format(template["tier"], template["id"], source["tier"], source["id"]))

        args = ["--image", source_file,
                "--mean", template_file,
                "--isovsize", iso_vsize_file]
        for warp_file in warp_files:
            args.extend(["--composed", warp_file])
        for invwarp_file in invwarp_files:
            args.extend(["--invcomposed", invwarp_file])
        args.extend(["--outcomposed", out_warp_file,
                     "--outinvcomposed", out_invwarp_file,
                     "--outwarped", warped_file,
                     "--outisowarped", isowarped_file])

        input_files = warp_files + invwarp_files + [source_file, iso_vsize_file]
        output_files = [warped_file, isowarped_file, out_warp_file, out_invwarp_file]

        for inputfile in input_files:
            self.pegasus_job.uses(inputfile, link=Link.INPUT)
        for outputfile in output_files:
            self.pegasus_job.uses(outputfile, link=Link.OUTPUT, transfer=transferflag)

        self.pegasus_job.addArguments(*args)
