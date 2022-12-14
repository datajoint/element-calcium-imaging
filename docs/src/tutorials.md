# Tutorials

## Installation

Installation of the Element requires an integrated development environment and database.
Instructions to setup each of the components can be found on the 
[User Instructions](datajoint.com/docs/elements/user-instructions) page. These 
instructions use the example 
[workflow for Element Calcium Imaging](https://github.com/datajoint/workflow-calcium-imaging), 
which can be modified for a user's specific experimental requirements. This example
workflow uses four Elements (Lab, Animal, Session, and Calcium Imaging) to construct a
complete pipeline, and is able to ingest experimental metadata and process calcium imaging
scans.

## Videos

Our [YouTube tutorial](https://www.youtube.com/watch?v=gFLn0GB1L30) gives an overview 
of the workflow files, notebooks, as well as core concepts related to calcium imaging analysis.
To try out Elements notebooks in an online Jupyter environment with access to example data, visit 
[CodeBook](https://codebook.datajoint.io/). (Calcium Imaging notebooks coming soon!)


## Notebooks

Each of the 
[notebooks](https://github.com/datajoint/workflow-calcium-imaging/tree/main/notebooks) in 
the workflow steps through ways to interact with the Element itself.

- [00-DataDownload](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/00-datadownload_optional.ipynb)
highlights how to use DataJoint tools to download a sample model for trying out the Element.

- [01-Configure](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/01-configure.ipynb)
helps configure your local DataJoint installation to point to the correct database.

- [02-WorkflowStructure](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/02-workflow-structure-optional.ipynb)
demonstrates the table architecture of the Element and key DataJoint basics for interacting with these tables.

- [03-Process](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/03-process.ipynb)
steps through adding data to the tables and analyzing a calcium imaging scan.

- [04-Automate](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/04-automate-optional.ipynb)
highlights the same steps as above, but utilizing all built-in automation tools.

- [05-Explore](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/05-explore.ipynb)
demonstrates the steps to fetch the results stored in the tables and plot them.

- [06-Drop](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/06-drop-optional.ipynb)
provides the steps for dropping all the tables to start fresh.

- [07-DownStreamAnalysis](https://github.com/datajoint/workflow-calcium-imaging/blob/main/notebooks/07-downstream-analysis-optional.ipynb)
demonstrates event- and trial-based analysis.

## EXTRACT
Analysis with the EXTRACT package is currently supported for single channel, single plane scans with using Suite2p for
motion correction. For processing with EXTRACT, please refer to the notebook 03-Process, set `processing_method="extract"`
in the ProcessingParamSet table, and provide the `params` attribute of the ProcessingParamSet in the `{'suite2p': {...}, 'extract': {...}}`
dictionary format. Please also install the [MATLAB engine](https://pypi.org/project/matlabengine/) API for Python.