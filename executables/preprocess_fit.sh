#!/bin/bash

#Accept Arguments
while [[ "$#" > 1 ]]; do case $1 in
    --help) show_help="True";;
    -h) show_help="True";;
    --lookupfile) lookup_file="$2";;
    --templateinputsfile) template_inputs_file="$2";;
    --resamplefile) resample_bool_file="$2";;
    --vsizefile) vsize_file="$2";;
    --isovsizefile) iso_vsize_file="$2";;
    --dimsizefile) dim_file="$2";;
    --orig) orig_template_file="$2";;
    --initial) initial_template_file="$2";;
    --srctemplate) existing_template_file="$2";;
    *);;
  esac; shift
done
