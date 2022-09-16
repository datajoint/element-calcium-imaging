# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: Python 3.9.13 ('ele')
#     language: python
#     name: python3
# ---

# # Download example dataset
#
# This workflow will need two-photon calcium imaging data collected from either ScanImage or Scanbox and the processed with Suite2p or CaImAn.  We provide an example dataset to be downloaded to run through the workflow. This notebook walks you through the process to download the dataset.
#
# [CodeBook](codebook.datajoint.io) users can skip this step.
#
# ## Install `djarchive-client`
#
# + The example dataset is hosted on `djarchive`, an AWS storage.
#
# + We provide a client package, [djarchive-client](https://github.com/datajoint/djarchive-client), to download the data which can be installed with pip:

# + language="bash"
# pip install git+https://github.com/datajoint/djarchive-client.git
# -

# ## Download imaging datasets using `djarchive-client`

import os
import djarchive_client
client = djarchive_client.client()

# Browse the datasets that are available on `djarchive`:

list(client.datasets())

# Each of the datasets have different versions associated with the version of the `workflow-calcium-imaging` package. Browse the revisions:

list(client.revisions())

# To download the dataset, let's prepare a root directory, for example in `/tmp`:

# mkdir /tmp/example_data

# Get the dataset revision with the current version of `workflow-calcium-imaging`:

from workflow_calcium_imaging import version
revision = version.__version__.replace('.', '_')
revision

# Run download for a given dataset and revision:

client.download('workflow-calcium-imaging-test-set', target_directory='/tmp/example_data', revision=revision)

# ## Directory structure
#
# + After downloading, the directory will be organized as follows:
#
#     ```
#     /tmp/example_data/
#     - subject3/
#         - 210107_run00_orientation_8dir/
#             - run00_orientation_8dir_000_000.sbx
#             - run00_orientation_8dir_000_000.mat
#             - suite2p/
#                 - combined
#                 - plane0
#                 - plane1
#                 - plane2
#                 - plane3
#     - subject7/
#         - session1
#             - suite2p
#                 - plane0
#     ```
#
# + subject 3 data is recorded with Scanbox and processed with Suite2p.
#
# + subject 7 data is recorded with ScanImage and processed with Suite2p.
#
# + `element-calcium-imaging` and `workflow-calcium-imaging` also support ingestion of data processed with CaImAn.
#
# + We will use the dataset for subject 3 as an example for the rest of the notebooks. If you use your own dataset for the workflow, change the path accordingly.
#
# ## Next step
#
# + In the next notebook ([01-configure](01-configure.ipynb)) we will set up the configuration file for the workflow.
