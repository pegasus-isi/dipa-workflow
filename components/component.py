#!/bin/python
from Pegasus.DAX3 import *
import os
import sys
import pandas

class Component(object):
    """
    Component parent class.
    """
    def __init__(self, matrix, hierarchy=["PROJECT", "ID"], name="Project", transferflag=True):
        self.name = name
        self.messages = []
        self.matrix = matrix.copy()
        self.files = {}
        self.hierarchy = hierarchy
        self.initial_steps = []
        self.final_steps = []
        self.transferflag = transferflag

    @classmethod
    def get_arg_mappings(cls):
        args = {}
        return args

    def add_to_dax(self, dax, process):
        return dax

    def save_files(self, root):
        for filename, contents in self.files.iteritems():
            with open(root+"/"+filename, "w") as f:
                f.write(contents)

    def reset_messages(self):
        self.messages = []
