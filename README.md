# dipa-workflow
Pegasus workflow for the DIPA Pipeline at Waisman Center at University
of Wisconsin Madison.

- The pipeline is set to be submitted from waisman cluster headnode
  guero.keck.waisman.wisc.edu.

- The pegasus configuration files can be found in the conf directory

- the example directory contains a sample input file NormalizeFile.csv
  that is used as input for the dax generator dipa.py

- To setup and run the workflow:
```
  DIPA [options] (--input <path> | -i <path>) (--project <path> | -p <path>) (--site <site> | -s <site>) [--tier <level>...]
```

- The outputs for the pipeline will appear in the outputs directory.

- To check the status with pegasus-analyzer:
```
  pegasus-analyzer ${ProjectDir}/working/condorsubmit #Where $ProjectDir is the directory specified by --project/-p in the command above.
```

- To modify DIPA for your site:
  * Update the conf/site_setup.sh script to suit your server configuration. Install any missing dependencies referenced there.
  * Update the conf/sites.xml file to suit your server configuration and/or destination.

## Example Workflows

### Registration
This is an example of registration (always non-hierarchical):
![Registration](/doc/example_registration.png)

### Normalization (Non-Hierarchical)
This is an example of non-hierarchical normalization:
![Non-Hierarchical Normalization](/doc/example_normalization_nohierarchy.png)

### Normalization (Hierarchical)
This is an example of non-hierarchical normalization (3 groups of 2):
![Hierarchical Normalization](/doc/example_normalization_hierarchy.png)
