# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py
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

# # Allen Institute Calcium Imaging Workshop
# September 22, 2022
# + In this notebook, we will show how to interact with a database in Python and how re-run an analysis.
#
# + Other notebooks in this directory describe the process for running the analysis steps in more detail.
#
# + This notebook is meant to be run on CodeBook (`https://codebook.datajoint.io`) which contains example data.
#
# First, some packages we'll use in this notebook...

import datajoint as dj 
import numpy as np
from matplotlib import pyplot
import os
import getpass

# ## Configuration

# These steps are taken from [01-configure](01-configure.ipynb). If you've already saved a config file, you can skip to the next section.

# Enter database credentials.  A DataJoint workflow requires a connection to an existing relational database. The connection setup parameters are defined in the `dj.config` python dictionary.

# + tags=[]
username_as_prefix = dj.config["database.user"] + "_img_"
dj.config['custom'] = {
    'database.prefix': username_as_prefix,
    'imaging_root_data_dir': '/home/'
}
# -

# Next, we'll use a prompt to securely save your password.

dj.config["database.password"] = getpass.getpass()

# Now to save these credentials.

dj.config.save_global()

# ## Populating the database

# Next, we'll populate these schema using some steps from [04-automate](04-automate-optional.ipynb). If your schema are already populated, you can skip this step. For more details on each of these steps, please visit [that notebook](04-automate-optional.ipynb). Additional steps ensure write permissions on output directories.

# +

from workflow_calcium_imaging.pipeline import session, imaging # import schemas
from workflow_calcium_imaging.ingest import ingest_subjects, ingest_sessions #csv loaders

import csv

sessions_csv_path = f"/home/{dj.config['database.user']}/sessions.csv"
with open(sessions_csv_path, 'w', newline='') as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(["subject","session_dir"])
    csv_writer.writerow(["subject3","inbox/0_1_0a2/subject3/210107_run00_orientation_8dir/"])

ingest_subjects(subject_csv_path="/home/user_data/subjects.csv")
ingest_sessions(session_csv_path=sessions_csv_path)

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

imaging.ProcessingParamSet.insert_new_params(
    processing_method='suite2p', 
    paramset_idx=0, 
    params=params_suite2p,
    paramset_desc='Calcium imaging analysis with Suite2p using default Suite2p parameters')
# -

# Next, we'll trigger the relevant `populate` commands.

# +
from workflow_calcium_imaging import process

process.run()
session_key = (session.Session & 'subject="subject3"').fetch('KEY')[0]
imaging.ProcessingTask.insert1(
    dict(
        session_key, 
        scan_id=0,
        paramset_idx=0,
        processing_output_dir='inbox/0_1_0a2/subject3/210107_run00_orientation_8dir/suite2p'
    ),
    skip_duplicates=True
)
process.run()
# -

# And then, we'll insert new Curation to trigger ingestion of curated results, followed by the same `process.run` automation.
#

key = (imaging.ProcessingTask & session_key).fetch1('KEY')
imaging.Curation().create1_from_processing_task(key)
process.run()

# ## Exploring the workflow
#
# ### Import the workflow
#
# The current workflow is composed of multiple database schemas, each of them corresponding to a module within the `workflow_calcium_imaging.pipeline` file.

from workflow_calcium_imaging.pipeline import lab, subject, session, scan, imaging

# ### Diagrams and table design
#
# We can plot the workflow diagram.  In relational databases, the entities (i.e. rows) in different tables are connected to each other. Visualization of this relationship helps one to write accurate queries. For the calcium imaging workflow, this connection is as follows:

# + tags=[]
dj.Diagram(lab.Lab) + dj.Diagram(subject.Subject) + dj.Diagram(session.Session) + \
dj.Diagram(scan) + dj.Diagram(imaging)
# -

subject.Subject()

scan.Scan()

imaging.Fluorescence()

# ### Fetch data
#
# Here, we fetch a fluorescence trace for a single mask and plot these values.

imaging.Fluorescence.Trace()

# Restrict the table with specific criteria.

query_trace = imaging.Fluorescence.Trace & 'subject="subject3"' \
                                    & 'session_datetime="2022-09-01 19:16:44"' \
                                    & 'mask=120'
query_trace

# Fetch a fluorescence trace from the database.

trace = (query_trace).fetch('fluorescence')[0]

# Plot the fluorescence trace.

# +
sampling_rate = (scan.ScanInfo & 'subject="subject3"' & 'session_datetime="2022-09-01 19:16:44"').fetch1('fps')

pyplot.plot(np.r_[:trace.size] * 1/sampling_rate, trace, 'k')

pyplot.title('Fluorescence trace for mask 120', fontsize=14)
pyplot.tick_params(labelsize=14)
pyplot.xlabel('Time (s)')
pyplot.ylabel('Activity (a.u.)')
# -

# ## Running an analysis
#
# The workflow has already been run for with a parameter set (`paramset_idx=1`).  Let's re-run Suite2p with a different parameter set, changing the cell diameter to 10 microns.

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
                  'nplanes': 4,
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
output_dir = f"{dj.config['database.user']}"
print(output_dir)
os.makedirs(output_dir, exist_ok=True)

imaging.ProcessingTask.insert1(
    dict(
        subject='subject3', 
        session_datetime='2022-09-01 19:16:44', 
        scan_id=0,
        paramset_idx=1,
        processing_output_dir=output_dir,
        task_mode='trigger'
    )
)
# -

imaging.ProcessingTask()

# You can then run Suite2p for the new parameter set and save the results to the respective tables. For this dataset (4 channels, 4 depths, 7.5k frames), this may take several hours.

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
