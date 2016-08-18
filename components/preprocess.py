#!/bin/python
from Pegasus.DAX3 import *
import os
import sys
import pandas

class preprocess(object):
    """
    Normalize component of DIPA.
    Uses DTI-TK to normalize subjects to an iteratively improved template, or a predefined one.
    matrix is assumed to be a pandas dataframe. "hierarchy" is a list referencing headers in the matrix.
    """
    def __init__(self, matrix, hierarchy=["PROJECT", "ID"], name="Project", eddy_correction="eddy", orient_check=True, fit_method="WLS", is_shelled=True, transferflag=True):
        self.name = name
        self.matrix = matrix.copy()

        self.hierarchy = hierarchy

        #Rework the matrix file:
        self.matrix["FULL_ID"] = matrix.apply(lambda row: self.__get_unique_matrix_key__(row), axis=1)

        self.matrix["BVAL_DEST"]

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

        self.initial_steps = []
        self.final_steps = []

    def __get_unique_matrix_key__(self, row):
        values = []
        for level in self.hierarchy:
            if level != "PROJECT":
                values.append(str(row[level]))
        return "_".join(values)
