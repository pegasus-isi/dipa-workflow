#============================================================================
#             Importing Things
#============================================================================

import sys
import math
import pandas
from console import Notice

#============================================================================
#             Console Class
#============================================================================

class matrixparser(object):
    "Processes a matrix."
    def __init__(self, matrix, hierarchy, name="Project", eddy_correction="eddy", is_shelled=True, template=None):
        self.name = name
        self.hierarchy = hierarchy
        self.eddy_correction = eddy_correction
        self.matrix = matrix
        self.is_shelled = is_shelled
        self.is_valid = False
        self.warnings = []
        if self.is_shelled == False and self.eddy_correction == "eddy":
            self.eddy_correction = "eddy_correct"
            self.warnings.append(Notice("Warning", "The data you specified was not shelled, so 'eddy' should not be used for eddy correction. Defaulting to 'eddy_correct'."))

        if "ID" not in self.hierarchy:
            self.hierarchy.append("ID")
        if "PROJECT" not in self.hierarchy:
            self.hierarchy = ["PROJECT"] + self.hierarchy

        if template != None:
            self.hierarchy = ["PROJECT", "ID"]

        if "PROJECT" not in self.matrix.columns:
            self.matrix["PROJECT"] = self.name

        expected_columns = self.hierarchy + ["DWI"]
        if self.eddy_correction == "eddy":
            expected_columns.extend(["MASK","BVALS","BVECS","INDEX","ACQPARAMS"])

        if set(expected_columns).issubset(set(self.matrix.columns)):
            self.is_valid = True
        else:
            missingcols = list(set(expected_columns).difference(set(self.matrix.columns)))
            self.warnings.append(Notice("Error", "You are missing required columns [{0}] in your input file.".format(", ".join(missingcols))))

        self.matrix["FULL"] = self.matrix.apply(lambda row: self.__get_unique_matrix_key__(row), axis=1)

        assembler = []
        for index, row in self.matrix.iterrows():
            assembler.append({"SOURCE":row["DWI"],"DESTINATION":row["FULL"]+"_dwi.nii.gz"})
            assembler.append({"SOURCE":row["BVALS"],"DESTINATION":row["FULL"]+"_bvals.txt"})
            assembler.append({"SOURCE":row["BVECS"],"DESTINATION":row["FULL"]+"_bvecs.txt"})
            if self.eddy_correction == "eddy":
                assembler.append({"SOURCE":row["MASK"],"DESTINATION":row["FULL"]+"_dwi_mask.nii.gz"})
                assembler.append({"SOURCE":row["INDEX"],"DESTINATION":row["FULL"]+"_index.txt"})
                assembler.append({"SOURCE":row["ACQPARAMS"],"DESTINATION":row["FULL"]+"_acqparams.txt"})

        if template != None:
            assembler.append({"SOURCE":template,"DESTINATION":self.name+"_template_orig.nii.gz"})
        self.mappings = pandas.DataFrame(assembler)

    def __get_unique_matrix_key__(self, row):
        values = []
        for level in self.hierarchy:
            values.append(level+"-"+str(row[level]))
        return "_".join(values)
