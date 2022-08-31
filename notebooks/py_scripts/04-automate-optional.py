# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: 'Python 3.7.9 64-bit (''workflow-calcium-imaging'': conda)'
#     name: python379jvsc74a57bd01a512f474e195e32ad84236879d3bb44800a92b431919ef0b10d543f5012a23c
# ---

# + [markdown] pycharm={"name": "#%% md\n"}
# # Run workflow in an automatic way
#
# In the previous notebook [03-process](03-process.ipynb), we ran through the workflow in detailed steps. For daily running routines, the current notebook provides a more succinct and automatic approach to run through the pipeline using some utility functions in the workflow.
# -

import os
if os.path.basename(os.getcwd()) == "notebooks": os.chdir("..")
import numpy as np
from workflow_calcium_imaging.pipeline import lab, subject, session, scan, imaging

# ## Ingestion of subjects, sessions, scans
#
# + Fill subject and session information in files `/user_data/subjects.csv` and `/user_data/sessions.csv`
#
# + Run automatic scripts prepared in `workflow_calcium_imaging.ingest` for ingestion: 
#
#     + `ingest_subjects` - ingests data into subject.Subject
#
#     + `ingest_sessions` - ingests data into Equipment, session.Session, session.SessionDirectory, scan.Scan

# +
from workflow_calcium_imaging.ingest import ingest_subjects, ingest_sessions

ingest_subjects()
ingest_sessions()
# -

# ## (Optional) Insert new ProcessingParamSet for Suite2p or CaImAn
#
# + This is not needed if you are using an existing ProcessingParamSet.

# + jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
params_suite2p = {'look_one_level_down': 0.0,
                  'fast_disk': [],
                  'delete_bin': False,
                  'mesoscan': False,
                  'h5py': [],
                  'h5py_key': 'data',
                  'save_path0': [],
                  'subfolders': [],
                  'nplanes': 1,
                  'nchannels': 1,
                  'functional_chan': 1,
                  'tau': 1.0,
                  'fs': 10.0,
                  'force_sktiff': False,
                  'preclassify': 0.0,
                  'save_mat': False,
                  'combined': True,
                  'aspect': 1.0,
                  'do_bidiphase': False,
                  'bidiphase': 0.0,
                  'do_registration': True,
                  'keep_movie_raw': False,
                  'nimg_init': 300,
                  'batch_size': 500,
                  'maxregshift': 0.1,
                  'align_by_chan': 1,
                  'reg_tif': False,
                  'reg_tif_chan2': False,
                  'subpixel': 10,
                  'smooth_sigma': 1.15,
                  'th_badframes': 1.0,
                  'pad_fft': False,
                  'nonrigid': True,
                  'block_size': [128, 128],
                  'snr_thresh': 1.2,
                  'maxregshiftNR': 5.0,
                  '1Preg': False,
                  'spatial_hp': 50.0,
                  'pre_smooth': 2.0,
                  'spatial_taper': 50.0,
                  'roidetect': True,
                  'sparse_mode': False,
                  'diameter': 12,
                  'spatial_scale': 0,
                  'connected': True,
                  'nbinned': 5000,
                  'max_iterations': 20,
                  'threshold_scaling': 1.0,
                  'max_overlap': 0.75,
                  'high_pass': 100.0,
                  'inner_neuropil_radius': 2,
                  'min_neuropil_pixels': 350,
                  'allow_overlap': False,
                  'chan2_thres': 0.65,
                  'baseline': 'maximin',
                  'win_baseline': 60.0,
                  'sig_baseline': 10.0,
                  'prctile_baseline': 8.0,
                  'neucoeff': 0.7,
                  'xrange': np.array([0, 0]),
                  'yrange': np.array([0, 0])}
# -

imaging.ProcessingParamSet.insert_new_params(
    processing_method='suite2p', 
    paramset_idx=0, 
    params=params_suite2p,
    paramset_desc='Calcium imaging analysis with Suite2p using default Suite2p parameters')

# ## Trigger autoprocessing of the remaining calcium imaging workflow

from workflow_calcium_imaging import process

# + The `process.run()` function in the workflow populates every auto-processing table in the workflow. If a table is dependent on a manual table upstream, it will not get populated until the manual table is inserted.
#
# + At this stage, process script populates through the table upstream of `ProcessingTask` (i.e. scan.ScanInfo)
#

process.run()

# ## Insert new ProcessingTask to trigger ingestion of processing results
#
# To populate the rest of the tables in the workflow, an entry in the `ProcessingTask` needs to be added to trigger the ingestion of the processing results, with the two pieces of information specified:
# + `paramset_idx` used for the processing job
# + output directory storing the processing results

# +
session_key = session.Session.fetch1('KEY')

imaging.ProcessingTask.insert1(dict(session_key, 
                                    scan_id=0,
                                    paramset_idx=0,
                                    processing_output_dir='subject3/210107_run00_orientation_8dir/suite2p'), skip_duplicates=True)
# -

# ## Run populate for table `imaging.Processing`

process.run()

# ## Insert new Curation to trigger ingestion of curated results

key = (imaging.ProcessingTask & session_key).fetch1('KEY')
imaging.Curation().create1_from_processing_task(key)

# ## Run populate for the rest of the tables in the workflow (takes a while)

process.run()

# ## Summary and next step
#
# + This notebook runs through the workflow in an automatic manner.
#
# + In the next notebook [05-explore](05-explore.ipynb), we will introduce how to query, fetch and visualize the contents we ingested into the tables.
