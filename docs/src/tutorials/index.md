# Tutorials

+ DataJoint Elements are modular pipelines that can be connected into a complete workflow.  [Workflow Calcium Imaging](https://github.com/datajoint/workflow-calcium-imaging) is an example that combines five DataJoint Elements - Lab, Animal, Session, Event, and Calcium Imaging.

+ Workflow Calcium Imaging includes an [interactive tutorial on GitHub Codespaces](https://github.com/datajoint/workflow-calcium-imaging#interactive-tutorial), which is configured for users to run the pipeline.

+ In the interactive tutorial, the [example notebook](https://github.com/datajoint/workflow-calcium-imaging/tree/main/notebooks/tutorial.ipynb) describes the pipeline and provides instructions for adding data to the pipeline.

## Installation Instructions for Active Projects

+ The Workflow Calcium Imaging described above can be modified for a user's specific experimental requirements and thereby used in active projects.  

+ The GitHub Codespace and Dev Container is configured for tutorials and prototyping.  
We recommend users to configure a database specifically for production pipelines.  Instructions for a local installation of the integrated development environment with a database can be found on the [User Guide](https://datajoint.com/docs/elements/user-guide/) page.

## Videos

Our [YouTube tutorial](https://www.youtube.com/watch?v=gFLn0GB1L30) gives an overview of
the workflow files and notebooks, as well as core concepts related to calcium imaging
analysis.

## Notebooks

Each of the notebooks in the workflow
([download here](https://github.com/datajoint/workflow-calcium-imaging/tree/main/notebooks)
steps through ways to interact with the Element itself. For convenience, these notebooks
are also rendered as part of this site. To try out the notebooks in an online
Jupyter environment with access to example data, visit
[CodeBook](https://codebook.datajoint.io/).

- [Data Download](./00-data-download-optional.ipynb) highlights how to use DataJoint
  tools to download an example dataset to try out the Element.

- [Configure](./01-configure.ipynb) helps configure your local DataJoint installation to
  point to the correct database.

- [Workflow Structure](./02-workflow-structure-optional.ipynb) demonstrates the table
  architecture of the Element and key DataJoint basics for interacting with these
  tables.

- [Process](./03-process.ipynb) steps through adding data to the tables and analyzing a
  calcium imaging scan.

- [Automate](./04-automate-optional.ipynb) highlights the same steps as above, but
  utilizing all built-in automation tools.

<!-- TODO: FIX UNICODE STRING ON ORIGINAL NOTEBOOK CAUSING CONVERSION ERROR
- [Explore](./05-explore.ipynb) demonstrates the steps to fetch the results stored in
  the tables and plot them. -->

- [Drop](./06-drop-optional.ipynb) provides the steps for dropping all the tables to
  start fresh.

- [Downstream Analysis](./07-downstream-analysis-optional.ipynb) demonstrates event- and
  trial-based analysis.


## EXTRACT

Analysis with the EXTRACT package is currently supported for single channel, single
plane scans with using Suite2p for motion correction. For processing with EXTRACT,
please refer to the notebook 03-Process, set `processing_method="extract"` in the
ProcessingParamSet table, and provide the `params` attribute of the ProcessingParamSet
table in the `{'suite2p': {...}, 'extract': {...}}` dictionary format. Please also
install the [MATLAB engine](https://pypi.org/project/matlabengine/) API for Python.
