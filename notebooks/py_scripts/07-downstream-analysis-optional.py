# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: venv-nwb
#     language: python
#     name: venv-nwb
# ---

# + [markdown] tags=[]
# # DataJoint U24 - Workflow Calcium Imaging

# + [markdown] tags=[]
# ## Setup
# -

# First, let's change directories to find the `dj_local_conf` file.

import os
# change to the upper level folder to detect dj_local_conf.json
if os.path.basename(os.getcwd())=='notebooks': os.chdir('..')
assert os.path.basename(os.getcwd())=='workflow-calcium-imaging', (
    "Please move to the workflow directory")
# We'll be working with long tables, so we'll make visualization easier with a limit
import datajoint as dj; dj.config['display.limit']=10

# Next, we populate the python namespace with the required schemas

from workflow_calcium_imaging.pipeline import session, imaging, trial, event

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# ## Trial and Event schemas
# -

# Tables in the `trial` and `event` schemas specify the structure of your experiment, including block, trial and event timing. 
# - Session has a 1-to-1 mapping with a behavior recording
# - A block is a continuous phase of an experiment that contains repeated instances of a condition, or trials. 
# - Events may occur within or outside of conditions, either instantaneous or continuous.
#
# The diagram below shows (a) the levels of hierarchy and (b) how the bounds may not completely overlap. A block may not fully capure trials and events may occur outside both blocks/trials.

# ```
# |----------------------------------------------------------------------------|
# |-------------------------------- Session ---------------------------------|__
# |-------------------------- BehaviorRecording ---------------------------|____
# |----- Block 1 -----|______|----- Block 2 -----|______|----- Block 3 -----|___
# | trial 1 || trial 2 |____| trial 3 || trial 4 |____| trial 5 |____| trial 6 |
# |_|e1|_|e2||e3|_|e4|__|e5|__|e6||e7||e8||e9||e10||e11|____|e12||e13|_________|
# |----------------------------------------------------------------------------|
# ```

# Let's load some example data. The `ingest.py` script has a series of loaders to help. If you've already run the other notebooks, you might skip `ingest_subjects` and `ingest_sessions`.

from workflow_calcium_imaging.ingest import ingest_subjects, ingest_sessions,\
                                            ingest_events, ingest_alignment

# ingest_subjects(); ingest_sessions()
ingest_events()

# We have 40 total trials, either 'stim' or 'ctrl', with start and stop time

trial.Trial()

# Each trial is paired with one or more events that take place during the trial window.

trial.TrialEvent() & 'trial_id<5'

# Finally, the `AlignmentEvent` describes the event of interest and the window we'd like to see around it.

ingest_alignment()

event.AlignmentEvent()

# + [markdown] tags=[]
# # Event-aligned trialized calcium activity
# -

from workflow_calcium_imaging import analysis

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# ### Analysis
# -

# The `analysis` schema provides example tables to perform event-aligned Calcium activity analysis.
# + ***ActivityAlignmentCondition*** - a manual table to specify the inputs and condition for the analysis
# + ***ActivityAlignment*** - a computed table to extract event-aligned Calcium activity (e.g. dF/F, spikes)

# Let's start by creating several analyses configuration - i.e. inserting into ***ActivityAlignmentCondition***

imaging.Activity()

# We'll isolate the scan of interest with the following key:

ca_activity_key = (imaging.Activity & {'subject': 'subject3', 'scan_id': 0}
                  ).fetch1('KEY')

# Here, we can see all trials for this scan:

trial.Trial & ca_activity_key

# And highlight a subset based on `trial_type`

ctrl_trials = trial.Trial & ca_activity_key & 'trial_type = "ctrl"'
ctrl_trials

# Here, we target the event of interest with another key:

alignment_key = (event.AlignmentEvent & 'alignment_name = "center_button"'
                ).fetch1('KEY')
alignment_key

alignment_condition = {**ca_activity_key, **alignment_key, 
                       'trial_condition': 'ctrl_center_button'}
alignment_condition

# Next, we add this to the `ActivityAlignment` table in the `analysis` schema

analysis.ActivityAlignmentCondition.insert1(alignment_condition, skip_duplicates=True)

analysis.ActivityAlignmentCondition()

# Using the [projection](https://docs.datajoint.org/python/v0.13/queries/08-Proj.html) method, we can generate a table of relevant trials by `trial_type` and `alignment_condition`

sample = (analysis.ActivityAlignmentCondition * ctrl_trials & alignment_condition).proj()
sample

# And insert these trials into the `ActivityAlignmentCondition.Trial` part table

analysis.ActivityAlignmentCondition.Trial.insert(sample, skip_duplicates=True)
analysis.ActivityAlignmentCondition.Trial()

# With the steps above, we have create a new alignment condition for analysis, named `ctrl_center_button`, which specifies:
# + an Activity of interest for analysis
# + an event of interest to align the Ca+ activity to - `center_button`
# + a set of trials of interest to perform the analysis on - `ctrl` trials
#
# ---

# Now, let's create another set with:
# + the same Activity of interest for analysis
# + an event of interest to align the Ca+ activity to - `center_button`
# + a set of trials of interest to perform the analysis on - `stim` trials

stim_trials = trial.Trial & ca_activity_key & 'trial_type = "stim"'
alignment_condition = {**ca_activity_key, **alignment_key, 
                       'trial_condition': 'stim_center_button'}
analysis.ActivityAlignmentCondition.insert1(alignment_condition, skip_duplicates=True)
analysis.ActivityAlignmentCondition.Trial.insert(
    (analysis.ActivityAlignmentCondition * stim_trials & alignment_condition).proj(),
    skip_duplicates=True)

# Note the two entries in `ActivityAlignmentCondition.trial_condition`

analysis.ActivityAlignmentCondition()

analysis.ActivityAlignmentCondition.Trial & 'trial_condition = "ctrl_center_button"'

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# ### Computation
# Just like the element itself, we can run computations with `populate()`
# -

analysis.ActivityAlignment.populate(display_progress=True)

analysis.ActivityAlignment()

# The `AlignedTrialActivity` part table captures aligned traces fore each alignment and trial condition specified in the master table.

analysis.ActivityAlignment.AlignedTrialActivity()

# ### Visualization

# With the `plot_aligned_activities` function, we can see the density of activity relative to our alignment event. For more information, see the corresponding docstring.

help(analysis.ActivityAlignment().plot_aligned_activities)

# For a refresher on the differences between masks, we can browse the `imaging.Segmentation.Mask` table.

imaging.Segmentation.Mask & 'mask<3'

# Then, we can directly compare the stimulus and control conditions relative to center button presses.

from workflow_calcium_imaging import analysis
from workflow_calcium_imaging.pipeline import session, imaging, trial, event
ca_activity_key = (imaging.Activity & {'subject': 'subject3', 'scan_id': 0}
                  ).fetch1('KEY')
alignment_key = (event.AlignmentEvent & 'alignment_name = "center_button"'
                ).fetch1('KEY')
alignment_condition_ctrl = {**ca_activity_key, **alignment_key, 
                            'trial_condition': 'ctrl_center_button'}
alignment_condition_stim = {**ca_activity_key, **alignment_key, 
                            'trial_condition': 'stim_center_button'}

analysis.ActivityAlignment().plot_aligned_activities(alignment_condition_stim, roi=2,
                                                     title='Stimulus Center Button');
analysis.ActivityAlignment().plot_aligned_activities(alignment_condition_ctrl, roi=2,
                                                     title='Control Center Button');


