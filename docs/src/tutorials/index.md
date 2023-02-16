# Tutorials

## Installation

Installation of the Element requires an integrated development environment and database.
Instructions to setup each of the components can be found on the
[User Instructions](https://datajoint.com/docs/elements/user-guide/) page. These
instructions use the example
[workflow for Element Calcium Imaging](https://github.com/datajoint/workflow-calcium-imaging),
which can be modified for a user's specific experimental requirements. This example
workflow uses four Elements (Lab, Animal, Session, and Calcium Imaging) to construct a
complete pipeline, and is able to ingest experimental metadata and process calcium
imaging scans.

## Videos

Our [YouTube tutorial](https://www.youtube.com/watch?v=gFLn0GB1L30) gives an overview of
the workflow files, notebooks, as well as core concepts related to calcium imaging
analysis. To try out Elements notebooks in an online Jupyter environment with access to
example data, visit
[CodeBook](https://codebook.datajoint.io/). (Calcium Imaging notebooks coming soon!)

## Notebooks

Each of the notebooks in the workflow
([download here](https://github.com/datajoint/workflow-calcium-imaging/tree/main/notebooks)
steps through ways to interact with the Element itself. For convenience, these notebooks
are also rendered as part of this site. To try out the Elements notebooks in an online
Jupyter environment with access to example data, visit
[CodeBook](https://codebook.datajoint.io/).

- [Data Download](./00-data-download-optional.ipynb) highlights how to use DataJoint
  tools to download a sample model for trying out the Element.

- [Configure](./01-configure.ipynb) helps configure your local DataJoint installation to
  point to the correct database.

- [WorkflowStructure](./02-workflow-structure-optional.ipynb) demonstrates the table
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

- [Workshop Demo](./2022-allen-institute-workshop.ipynb) provides a brief overview of
  all of the above for a workshop setting.

## EXTRACT

Analysis with the EXTRACT package is currently supported for single channel, single
plane scans with using Suite2p for motion correction. For processing with EXTRACT,
please refer to the notebook 03-Process, set `processing_method="extract"` in the
ProcessingParamSet table, and provide the `params` attribute of the ProcessingParamSet
table in the `{'suite2p': {...}, 'extract': {...}}` dictionary format. Please also
install the [MATLAB engine](https://pypi.org/project/matlabengine/) API for Python.
