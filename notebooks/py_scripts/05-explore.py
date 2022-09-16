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

# # DataJoint Workflow Calcium Imaging
#
# + This notebook will describe the steps for interacting with the data ingested into `workflow-calcium-imaging`.  

import os
if os.path.basename(os.getcwd()) == "notebooks": os.chdir("..")

# +
import datajoint as dj
import matplotlib.pyplot as plt
import numpy as np

from workflow_calcium_imaging.pipeline import lab, subject, session, scan, imaging
# -

# ## Workflow architecture
#
# This workflow is assembled from 4 DataJoint elements:
# + [element-lab](https://github.com/datajoint/element-lab)
# + [element-animal](https://github.com/datajoint/element-animal)
# + [element-session](https://github.com/datajoint/element-session)
# + [element-calcium-imaging](https://github.com/datajoint/element-calcium-imaging)
#
# For the architecture and detailed descriptions for each of those elements, please visit the respective links. 
#
# Below is the diagram describing the core components of the fully assembled pipeline.
#

dj.Diagram(imaging) + dj.Diagram(scan) + (dj.Diagram(session.Session) + 1) - 1

# ## Browsing the data with DataJoint `query` and `fetch` 
#
# + DataJoint provides functions to query data and fetch.  For a detailed tutorials, visit our [general tutorial site](https://playground.datajoint.io/).
#
# + Running through the pipeline, we have ingested data of subject3 into the database.
#
# + Here are some highlights of the important tables.
#
# ### `subject.Subject` and `session.Session` tables

subject.Subject()

session.Session()

# + Fetch the primary key for the session of interest which will be used later on in this notebook.

session_key = (session.Session & 'subject = "subject3"').fetch('KEY')[0]

# ### `scan.Scan` and `scan.ScanInfo` tables
#
# + These tables stores the scan metadata within a particular session.

scan.Scan & session_key

scan.ScanInfo & session_key

scan.ScanInfo.Field & session_key

# ### `imaging.ProcessingParamSet`, `imaging.ProcessingTask`, `imaging.Processing`, and `imaging.Curation` tables
#
# + The parameters used for Suite2p or CaImAn are stored in `imaging.ProcessingParamSet` under a `paramset_idx`.
#
# + The processing details for Suite2p and CaImAn are stored in `imaging.ProcessingTask` and `imaging.Processing` for the utilized `paramset_idx`.
#
# + After the motion correction and segmentation, the results may go through a curation process. 
#     
#     + If it did not go through curation, a copy of the `imaging.ProcessingTask` entry is inserted into `imaging.Curation` with the `curation_output_dir` identical to the `processing_output_dir`.
#
#     + If it did go through a curation, a new entry will be inserted into `imaging.Curation`, with a `curation_output_dir` specified.
#
#     + `imaging.Curation` supports multiple curations of an entry in `imaging.ProcessingTask`.

imaging.ProcessingParamSet()

imaging.ProcessingTask * imaging.Processing & session_key

# In this example workflow, `curation_output_dir` is the same as the `processing_output_dir`, as these results were not manually curated.

imaging.Curation & session_key

# ### `imaging.MotionCorrection` table
#
# + After processing and curation, results are passed to the `imaging.MotionCorrection` and `imaging.Segmentation` tables.
#
# + For the example data, the raw data is corrected with rigid and non-rigid motion correction which is stored in `imaging.MotionCorrection.RigidMotionCorrection` and `imaging.MotionCorrection.NonRigidMotionCorrection`, respectively. 
#
# + Lets first query the information for one curation.

curation_key = (imaging.Curation & session_key & 'curation_id=0').fetch1('KEY')

curation_key

imaging.MotionCorrection.RigidMotionCorrection & curation_key

imaging.MotionCorrection.NonRigidMotionCorrection & curation_key

# + For non-rigid motion correction, the details for the individual blocks are stored in `imaging.MotionCorrection.Block`.

imaging.MotionCorrection.Block & curation_key & 'block_id=0'

# + Summary images are stored in `imaging.MotionCorrection.Summary`
#
#     + Reference image - image used as an alignment template
#
#     + Average image - mean of registered frames
#
#     + Correlation image - correlation map (computed during region of interest \[ROI\] detection)
#
#     + Maximum projection image - max of registered frames

imaging.MotionCorrection.Summary & curation_key & 'field_idx=0'

# + Lets fetch the `average_image` and plot it.

average_image = (imaging.MotionCorrection.Summary & curation_key & 'field_idx=0').fetch1('average_image')

plt.imshow(average_image);

# ### `imaging.Segmentation` table
#
# + Lets fetch and plot a mask stored in the `imaging.Segmentation.Mask` table for one `curation_id`.
#
# + Each mask can be associated with a field by the attribute `mask_center_z`.  For example, masks with `mask_center_z=0` are in the field identified with `field_idx=0` in `scan.ScanInfo.Field`.

mask_xpix, mask_ypix = (imaging.Segmentation.Mask * imaging.MaskClassification.MaskType & curation_key & 'mask_center_z=0' & 'mask_npix > 130').fetch('mask_xpix','mask_ypix')

mask_image = np.zeros(np.shape(average_image), dtype=bool)
for xpix, ypix in zip(mask_xpix, mask_ypix):
    mask_image[ypix, xpix] = True

plt.imshow(average_image);
plt.contour(mask_image, colors='white', linewidths=0.5);

# ### `imaging.MaskClassification` table
#
# + This table provides the `mask_type` and `confidence` for the mask classification.

imaging.MaskClassification.MaskType & curation_key & 'mask=0'

# ### `imaging.Fluorescence` and `imaging.Activity` tables
#
# + Lets fetch and plot the flourescence and activity traces for one mask.

query_cells = (imaging.Segmentation.Mask * imaging.MaskClassification.MaskType & curation_key & 'mask_center_z=0' & 'mask_npix > 130').proj()

# +
fluorescence_traces = (imaging.Fluorescence.Trace & query_cells).fetch('fluorescence', order_by='mask')

activity_traces = (imaging.Activity.Trace & query_cells).fetch('activity_trace', order_by='mask')

sampling_rate = (scan.ScanInfo & curation_key).fetch1('fps') # [Hz]

# +
fig, ax = plt.subplots(1, 1, figsize=(16, 4))
ax2 = ax.twinx()

for f, a in zip(fluorescence_traces, activity_traces):
    ax.plot(np.r_[:f.size] * 1/sampling_rate, f, 'k', label='fluorescence trace')    
    ax2.plot(np.r_[:a.size] * 1/sampling_rate, a, 'r', alpha=0.5, label='deconvolved trace')
    
    break

ax.tick_params(labelsize=14)
ax2.tick_params(labelsize=14)

ax.legend(loc='upper left', prop={'size': 14})
ax2.legend(loc='upper right', prop={'size': 14})

ax.set_xlabel('Time (s)')
ax.set_ylabel('Activity (a.u.)')
ax2.set_ylabel('Activity (a.u.)');
# -

# ## Summary and Next Step
#
# + This notebook highlights the major tables in the workflow and visualize some of the ingested results. 
#
# + The next notebook [06-drop](06-drop-optional.ipynb) shows how to drop schemas and tables if needed.
