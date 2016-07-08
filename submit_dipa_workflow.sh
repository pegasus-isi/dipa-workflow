#!/bin/bash

set -e

# this variable is expanded by the planner when
# parsing in the sites.xml file in the conf directory
TOPDIR=`pwd`
export TOPDIR

# pegasus bin directory is needed to find keg
BIN_DIR=`pegasus-config --bin`
PEGASUS_LOCAL_BIN_DIR=$BIN_DIR
export PEGASUS_LOCAL_BIN_DIR

# generate the dax
export PYTHONPATH=`pegasus-config --python`
./dipa.py --input-dir ./input --input-file ./example/NormalizeFile.csv --output-dax dipa.dax

export EXECUTABLE_DIR=$TOPDIR/executables

# plan and submit the  workflow
pegasus-plan \
    --conf ./conf/pegasusrc \
    --sites waisman \
    --input input \
    --output-site local \
    --dir dags \
    --dax dipa.dax \
    --force \
    --cleanup none \
    -vv \

    
