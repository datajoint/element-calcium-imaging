import datajoint as dj
import numpy as np

from workflow_calcium_imaging.pipeline import db_prefix, session, scan, imaging, trial, event


schema = dj.schema(db_prefix + 'analysis')


@schema
class ActivityAlignmentCondition(dj.Manual):
    definition = """
    -> imaging.Activity
    -> event.AlignmentEvent
    trial_condition: varchar(128) # user-friendly name of condition
    ---
    condition_description='': varchar(1000)
    bin_size=0.04: float # bin-size (in second) used to compute the PSTH
    """

    class Trial(dj.Part):
        definition = """  # Trials (or subset of trials) to computed event-aligned activity
        -> master
        -> trial.Trial
        """


@schema
class ActivityAlignment(dj.Computed):
    definition = """
    -> ActivityAlignmentCondition
    ---
    aligned_timestamps = longblob
    """

    class AlignedTrialSpikes(dj.Part):
        definition = """
        -> master
        -> imaging.Activity.Trace
        -> ActivityAlignmentCondition.Trial
        ---
        aligned_trace: longblob  # (s) Calcium activity aligned to the event time
        """

    def make(self, key):
        sess_time, scan_time, nframes, frame_rate = (scan.ScanInfo * session.Session & key).fetch1(
            'session_datetime', 'scan_datetime', 'nframes', 'fps')

        # Estimation of frame timestamps with respect to the session-start
        # (to be replaced by timestamps retrieved from some synchronization routine)
        scan_start = (scan_time - sess_time).total_seconds() if scan_time else 0
        frame_timestamps = np.arange(nframes) / frame_rate + scan_start

        trialized_event_times = trial.get_trialized_alignment_event_times(
            key, trial.Trial & (ActivityAlignmentCondition.Trial & key))

        min_limit = (trialized_event_times.event - trialized_event_times.start).max()
        max_limit = (trialized_event_times.end - trialized_event_times.event).max()

        # Spike raster
        trace_keys, activity_traces = (imaging.Activity.Trace & key).fetch('KEY', 'activity_trace', order_by='mask')
        activity_traces = np.hstack(activity_traces)

        aligned_trial_activities = []
        for _, r in trialized_event_times.iterrows():
            if np.isnan(r.event):
                continue
            alignment_start_time = r.event - min_limit
            alignment_end_time = r.event + max_limit
            roi_aligned_activities = activity_traces[:, (alignment_start_time <= frame_timestamps)
                                                        & (frame_timestamps < alignment_end_time)]

            aligned_trial_activities.extend([{**key, **r.trial_key, **trace_key, 'aligned_trace': aligned_trace}
                                             for trace_key, aligned_trace in zip(trace_keys, roi_aligned_activities)])

        self.insert1({**key, 'aligned_timestamps': np.linspace(
            -min_limit, max_limit, len(aligned_trial_activities[0]['aligned_trace']))})
        self.AlignedTrialSpikes.insert(aligned_trial_activities)

    def plot_aligned_activities(self, key, roi, axs=None):
        import matplotlib.pyplot as plt

        fig = None
        if axs is None:
            fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(12, 8))
        else:
            ax0, ax1 = axs

        aligned_timestamps = (self & key).fetch1('aligned_trace')
        trial_ids, aligned_spikes = (self.AlignedTrialSpikes
                                     & key & {'mask': roi}).fetch('trial_id', 'aligned_trace', order_by='trial_id')

        aligned_spikes = np.hstack(aligned_spikes)

        ax0.imshow(aligned_spikes, cmap='gray', interpolation='nearest')
        ax0.axvline(x=0, linestyle='--', color='white')
        ax0.set_xticks([])
        ax0.set_yticks([])

        ax1.plot(aligned_timestamps, np.nanmean(aligned_spikes))
        ax1.axvline(x=0, linestyle='--', color='black')
        ax1.set_xlabel('Time (s)')

        return fig
