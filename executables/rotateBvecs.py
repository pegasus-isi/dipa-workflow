#!../Python/bin/python
import string, os, sys, subprocess
import math as M
from numpy import matrix
from numpy import linalg

#Use MRIConvert to convert images to nifti format.  Images will be saved as a 4D file and then split into separate flip angles



if len(sys.argv[1:]) < 2:
	# print 'Correct Usage: python rotateBvecs.py <original bvec file> <output from FSL eddy (basename.eddy_parameters) < output path >'
	print 'Correct Usage: python rotateBvecs.py <original bvec file> <output from FSL eddy (basename.eddy_parameters)> <output file>'
	sys.exit(1)

input = sys.argv[1:]
bvecsFile = input[0]
eddyParamFile = input[1]
# outputRoot = input[2]

bvecData =open(bvecsFile, "r")
bvecs = bvecData.readlines()

x_bvec = bvecs[0].rstrip('\n').split()
y_bvec = bvecs[1].rstrip('\n').split()
z_bvec = bvecs[2].rstrip('\n').split()

eddyParamData = open(eddyParamFile, "r")
eddyParams = eddyParamData.readlines()

x_bvec_rot = ""
y_bvec_rot = ""
z_bvec_rot = ""

for i in range(0, len(eddyParams)):

    vol_params = eddyParams[i].rstrip('\n').split()

    theta_x = float(vol_params[4])
    theta_y = float(vol_params[5])
    theta_z = float(vol_params[6])

    R_x = matrix( [[1,0,0],[0,M.cos(theta_x),M.sin(theta_x)],[0,-M.sin(theta_x),M.cos(theta_x)]])
    R_y = matrix( [[M.cos(theta_y),0,-M.sin(theta_y)],[0,1,0],[M.sin(theta_y),0,M.cos(theta_y)]])
    R_z = matrix( [[M.cos(theta_z),M.sin(theta_z),0],[-M.sin(theta_z), M.cos(theta_z),0],[0,0,1]])

    R = (R_z.T)*(R_y.T)*(R_x.T)

    bx = float(x_bvec[i])
    by = float(y_bvec[i])
    bz = float(z_bvec[i])

    x = matrix( [[bx],[by],[bz]] )
    x_rot = R*x

    x_bvec_rot += str(x_rot.item(0)) + " "
    y_bvec_rot += str(x_rot.item(1)) + " "
    z_bvec_rot += str(x_rot.item(2)) + " "




# outputFilePath = outputRoot + "corrected_bvecs.bvec"
outputFilePath = input[2]
outputFile = open(outputFilePath, "w")

outputFile.write(x_bvec_rot+"\n")
outputFile.write(y_bvec_rot+"\n")
outputFile.write(z_bvec_rot+"\n")

outputFile.close()
