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

# # DataJoint configuration
#
# ## Setup - Working Directory
#
# To run the workflow, we need to properly set up the DataJoint configuration. The configuration can be saved in a local directory as `dj_local_conf.json` or at your root directory as a hidden file. This notebook walks you through the setup process.
#
# **The configuration only needs to be set up once**, if you have gone through the configuration before, directly go to [02-workflow-structure](02-workflow-structure-optional.ipynb).

import os
if os.path.basename(os.getcwd()) == "notebooks": os.chdir("..")
import datajoint as dj

import datajoint as dj

# ## Setup - Credentials
#
# Now let's set up the host, user and password in the `dj.config` global variable

import getpass
dj.config["database.host"] = "{YOUR_HOST}" # CodeBook users should omit this
dj.config["database.user"] = "{YOUR_USERNAME}"
dj.config["database.password"] = getpass.getpass()  # enter the password securely

# You should be able to connect to the database at this stage.

dj.conn()

# ## Setup - `dj.config['custom']`
#
# The major component of the current workflow is the [DataJoint Calcium Imaging Element](https://github.com/datajoint/element-array-ephys). Calcium Imaging Element requires configurations in the field `custom` in `dj.config`:
#
# ### Database prefix
#
# Giving a prefix to schema could help on the configuration of privilege settings. For example, if we set prefix `neuro_`, every schema created with the current workflow will start with `neuro_`, e.g. `neuro_lab`, `neuro_subject`, `neuro_scan` etc.
#
# The prefix could be configured in `dj.config` as follows. CodeBook users should keep their username as the prefix for schema declaration permissions.

username_as_prefix = dj.config["database.user"] + "_"
dj.config["custom"] = {"database.prefix": username_as_prefix}

# ### Root directories for raw/processed data
#
# `imaging_root_data_dir` field indicates the root directory for
# + The **raw data** from ScanImage or Scanbox (e.g. `*.tif`)
# + The processed results from Suite2p or CaImAn (e.g. `F.npy`). 
#
# This can be specific to each machine. The root path typically **does not** contain information of subjects or sessions, all data from subjects/sessions should be subdirectories in the root path.
#
# + In the example dataset downloaded with [these instructions](00-data-download-optional.ipynb), `/tmp/test_data` will be the root. 
# + For CodeBook users, the root is `/home/inbox/0_1_0a2/`
#
# ```
# subject3
# └── 210107_run00_orientation_8dir
#     ├── run00_orientation_8dir_000_000.mat
#     ├── run00_orientation_8dir_000_000.sbx
#     └── suite2p
#         ├── combined # same as plane0, plane1, plane2, and plane3
#         │   ├── F.npy
#         │   ├── Fneu.npy
#         │   ├── iscell.npy
#         │   ├── ops.npy
#         │   ├── spks.npy
#         │   └── stat.npy
#         └── run.log
# ```

#

# If using our example dataset, downloaded with this notebook [00-data-download](00-data-download-optional.ipynb), the root directory will be:

dj.config['custom']['imaging_root_data_dir'] = '/tmp/example_data' # local download
dj.config['custom']['imaging_root_data_dir'] = '/home/inbox/0_1_0a2/' # on CodeBook

dj.config

# ## Save configuration
#
# We could save this as a file, either as a local json file, or a global file. Local configuration file is saved as `dj_local_conf.json` in current directory, which is great for project-specific settings.
#
# For first-time and CodeBook users, we recommend saving globally. This will create a hidden configuration file saved in your root directory, loaded whenever there is no local version to override it.

# dj.config.save_local()
dj.config.save_global()

# ## Next Step
#
# After the configuration, we will be able to run through the workflow with the [02-workflow-structure](02-workflow-structure-optional.ipynb) notebook.
