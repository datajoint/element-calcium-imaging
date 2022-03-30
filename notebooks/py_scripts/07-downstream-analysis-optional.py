# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python [conda env:workflow-calcium-imaging]
#     language: python
#     name: conda-env-workflow-calcium-imaging-py
# ---

# cd ..

from workflow_calcium_imaging.pipeline import session, imaging, trial, event

from workflow_calcium_imaging import analysis

# # Event-aligned trialized Calcium activity

# The `analysis` schema provides example tables to perform event-aligned Calcium activity analysis.
# + ***ActivityAlignmentCondition*** - a manual table to specify the inputs and condition for the analysis
# + ***ActivityAlignment*** - a computed table to extract event-aligned Calcium activity (e.g. dF/F, spikes)

# Let's start by creating several analyses configuration - i.e. inserting into ***ActivityAlignmentCondition***

imaging.Activity()

ca_activity_key = (imaging.Activity & {'subject': 'subject3', 'session_datetime': '2021-01-28 14:56:52', 'scan_id': 0}).fetch1('KEY')

event.AlignmentEvent()

alignment_key = (event.AlignmentEvent & 'alignment_name = "center_button"').fetch1('KEY')

trial.Trial & ca_activity_key

ctrl_trials = trial.Trial & ca_activity_key & 'trial_type = "ctrl"'

alignment_condition = {**ca_activity_key, **alignment_key, 'trial_condition': 'ctrl_center_button'}

analysis.ActivityAlignmentCondition.insert1(alignment_condition, skip_duplicates=True)

analysis.ActivityAlignmentCondition.Trial.insert(
    (analysis.ActivityAlignmentCondition * ctrl_trials & alignment_condition).proj(),
    skip_duplicates=True)

# With the steps above, we have create a new spike alignment condition for analysis, named `ctrl_center_button`, which specifies:
# + an Activity of interest for analysis
# + an event of interest to align the Ca+ activity to - `center_button`
# + a set of trials of interest to perform the analysis on - `ctrl` trials

# Now, let's create another set with:
# + the same Activity of interest for analysis
# + an event of interest to align the Ca+ activity to - `center_button`
# + a set of trials of interest to perform the analysis on - `stim` trials

stim_trials = trial.Trial & ca_activity_key & 'trial_type = "stim"'
alignment_condition = {**ca_activity_key, **alignment_key, 'trial_condition': 'stim_center_button'}
analysis.ActivityAlignmentCondition.insert1(alignment_condition, skip_duplicates=True)
analysis.ActivityAlignmentCondition.Trial.insert(
    (analysis.ActivityAlignmentCondition * stim_trials & alignment_condition).proj(),
    skip_duplicates=True)

analysis.ActivityAlignmentCondition()

analysis.ActivityAlignmentCondition.Trial & 'trial_condition = "ctrl_center_button"'

# ### Now let's run the computation on these

analysis.ActivityAlignment.populate(display_progress=True)

# ### Let's visualize the results

alignment_condition = {**ca_activity_key, **alignment_key, 'trial_condition': 'ctrl_center_button'}
analysis.ActivityAlignment().plot_aligned_activities(alignment_condition, unit=2);

alignment_condition = {**ca_activity_key, **alignment_key, 'trial_condition': 'stim_center_button'}
analysis.ActivityAlignment().plot_aligned_activities(alignment_condition, unit=2);


