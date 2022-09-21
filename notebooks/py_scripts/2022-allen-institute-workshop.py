# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.0
#   kernelspec:
#     display_name: Python 3.7.9 ('workflow-calcium-imaging')
#     language: python
#     name: python3
# ---

# # Allen Institute Calcium Imaging Workshop
# September 22, 2022
# + In this notebook, we will show how to interact with a database in Python and how re-run an analysis.
#
# + Other notebooks in this directory describe the process for running the analysis steps in more detail.
#
# + This notebook is meant to be run on CodeBook (`https://codebook.datajoint.io`) which contains example data.
#
# + First run the `01-configure` and `04-automate` notebooks to set up your environment and load example data into the database, respectively.

# ## Configuration
#
# Import the relevant packages.

import datajoint as dj
import numpy as np
from matplotlib import pyplot
import os

# Enter database credentials.  A DataJoint workflow requires a connection to an existing relational database. The connection setup parameters are defined in the `dj.config` python dictionary.

# + tags=[]
dj.config['custom'] = {'database.prefix': '<username>_allen_ophys_',
                       'imaging_root_data_dir': '/home/inbox/0_1_0a2/'}
# -

# Import the workflow.  The current workflow is composed of multiple database schemas, each of them corresponding to a module within the `workflow_calcium_imaging.pipeline` file.

from workflow_calcium_imaging.pipeline import lab, subject, session, scan, imaging

# ## Workflow diagram
#
# Plot the workflow diagram.  In relational databases, the entities (i.e. rows) in different tables are connected to each other. Visualization of this relationship helps one to write accurate queries. For the calcium imaging workflow, this connection is as follows:

# + tags=[]
dj.Diagram(lab.Lab) + dj.Diagram(subject.Subject) + dj.Diagram(session.Session) + \
dj.Diagram(scan) + dj.Diagram(imaging)
# -

subject.Subject()

scan.Scan()

imaging.Fluorescence()

# ## Fetch data from the database
#
# Fetch a fluorescence trace for a single mask and plot these values.

imaging.Fluorescence.Trace()

# Restrict the table with specific criteria.

imaging.Fluorescence.Trace & 'subject="subject3"' \
                           & 'session_datetime="2022-09-01 19:16:44"' \
                           & 'mask_id=120'

# Fetch a fluorescence trace from the database.

trace = (imaging.Fluorescence.Trace & 'subject="subject3"' \
                                    & 'session_datetime="2022-09-01 19:16:44"' \
                                    & 'mask_id=120').fetch('fluorescence')

# Plot the fluorescence trace.

# +
sampling_rate = (scan.ScanInfo & 'subject="subject3"' & 'session_datetime="2022-09-01 19:16:44"').fetch1('fps')

pyplot.plot(np.r_[:trace.size] * 1/sampling_rate, trace, 'k')

pyplot.title('Fluorescence trace for mask 120',labelsize=14)
pyplot.tick_params(labelsize=14)
pyplot.set_xlabel('Time (s)')
pyplot.set_ylabel('Activity (a.u.)')
# -

# ## Run analysis
#
# The workflow has already been run for with a parameter set (paramset_idx=1).  Let's re-run Suite2p with a different parameter set, changing the cell diameter to 10 microns.

dj.Diagram(imaging.Processing)-2

imaging.ProcessingTask()

imaging.ProcessingParamSet()

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
                  'diameter': 10,
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

imaging.ProcessingParamSet.insert_new_params(processing_method='suite2p', 
                                             paramset_idx=1, 
                                             params=params_suite2p,
                                             paramset_desc='diameter=10')

imaging.ProcessingParamSet()

# +
os.makedirs('/home/inbox/0_1_0a2/subject3/210107_run00_orientation_8dir/suite2p_1', exist_ok=True)

imaging.ProcessingTask.insert1(dict(subject='subject3', 
                                    session_datetime='2022-09-01 19:16:44', 
                                    scan_id=0,
                                    paramset_idx=1,
                                    processing_output_dir='subject3/210107_run00_orientation_8dir/suite2p_1'))
# -

imaging.ProcessingTask()

# Run Suite2p for the new parameter set and save the results to the respective tables.

# +
populate_settings = dict(display_progress=True)

imaging.Processing.populate(**populate_settings)

key = (imaging.ProcessingTask & 'subject="subject3"' & 'session_datetime="2022-09-01 19:16:44"').fetch1('KEY')

imaging.Curation().create1_from_processing_task(key)

imaging.MotionCorrection.populate(**populate_settings)

imaging.Segmentation.populate(**populate_settings)

imaging.Fluorescence.populate(**populate_settings)

imaging.Activity.populate(**populate_settings)
# -

# ## Summary and next steps
#
# In this notebook we explored how to query and fetch data from the database, and re-run analysis with new parameters.  Next, please explore more of the features of the DataJoint Elements in the other notebooks.  Once you are ready to begin setting up your pipeline, fork this repository on GitHub and begin adapting it for your projects requirements.
