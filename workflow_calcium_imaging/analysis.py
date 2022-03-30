import datajoint as dj
import numpy as np

from workflow_calcium_imaging.pipeline import db_prefix, session, scan, imaging, trial, \
                                              event


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
        definition = """  # Trials (or subset) to compute event-aligned activity
        -> master
        -> trial.Trial
        """


@schema
class ActivityAlignment(dj.Computed):
    definition = """
    -> ActivityAlignmentCondition
    ---
    aligned_timestamps: longblob
    """

    class AlignedTrialActivity(dj.Part):
        definition = """
        -> master
        -> imaging.Activity.Trace
        -> ActivityAlignmentCondition.Trial
        ---
        aligned_trace: longblob  # (s) Calcium activity aligned to the event time
        """

    def make(self, key):
        sess_time, scan_time, nframes, frame_rate = (scan.ScanInfo * session.Session
                                                     & key
                                                     ).fetch1('session_datetime',
                                                              'scan_datetime',
                                                              'nframes', 'fps')

        # Estimation of frame timestamps with respect to the session-start
        # (to be replaced by timestamps retrieved from some synchronization routine)
        scan_start = (scan_time - sess_time).total_seconds() if scan_time else 0
        frame_timestamps = np.arange(nframes) / frame_rate + scan_start

        trialized_event_times = trial.get_trialized_alignment_event_times(
            key, trial.Trial & (ActivityAlignmentCondition.Trial & key))

        min_limit = (trialized_event_times.event - trialized_event_times.start).max()
        max_limit = (trialized_event_times.end - trialized_event_times.event).max()

        aligned_timestamps = np.arange(-min_limit, max_limit, 1/frame_rate)
        nsamples = len(aligned_timestamps)

        trace_keys, activity_traces = (imaging.Activity.Trace & key
                                       ).fetch('KEY', 'activity_trace', order_by='mask')
        activity_traces = np.vstack(activity_traces)

        aligned_trial_activities = []
        for _, r in trialized_event_times.iterrows():
            if r.event is None or np.isnan(r.event):
                continue
            alignment_start_idx = int((r.event - min_limit) * frame_rate)
            roi_aligned_activities = activity_traces[:,
                                                     alignment_start_idx:
                                                     (alignment_start_idx + nsamples)]
            if roi_aligned_activities.shape[-1] != nsamples:
                shape_diff = nsamples - roi_aligned_activities.shape[-1]
                roi_aligned_activities = np.pad(roi_aligned_activities,
                                                ((0, 0), (0, shape_diff)),
                                                mode='constant', constant_values=np.nan)

            aligned_trial_activities.extend([{**key, **r.trial_key, **trace_key,
                                              'aligned_trace': aligned_trace}
                                             for trace_key, aligned_trace
                                             in zip(trace_keys,
                                                    roi_aligned_activities)])

        self.insert1({**key, 'aligned_timestamps': aligned_timestamps})
        self.AlignedTrialActivity.insert(aligned_trial_activities)

    def plot_aligned_activities(self, key, roi, axs=None, title=None):
        """
        peri-stimulus time histogram (PSTH) for calcium imaging spikes
        :param key: key of ActivityAlignment master table
        :param roi: imaging segmentation mask
        :param axs: optional definition of axes for plot.
                    Default is plt.subplots(2, 1, figsize=(12, 8))
        :param title: Optional title label
        """
        import matplotlib.pyplot as plt

        fig = None
        if axs is None:
            fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(12, 8))
        else:
            ax0, ax1 = axs

        aligned_timestamps = (self & key).fetch1('aligned_timestamps')
        trial_ids, aligned_spikes = (self.AlignedTrialActivity
                                     & key & {'mask': roi}).fetch(
            'trial_id', 'aligned_trace', order_by='trial_id')

        aligned_spikes = np.vstack(aligned_spikes)

        ax0.imshow(aligned_spikes, cmap='inferno',
                   interpolation='nearest', aspect='auto',
                   extent=(aligned_timestamps[0],
                           aligned_timestamps[-1],
                           0,
                           aligned_spikes.shape[0]))
        ax0.axvline(x=0, linestyle='--', color='white')
        ax0.set_axis_off()

        ax1.plot(aligned_timestamps, np.nanmean(aligned_spikes, axis=0))
        ax1.axvline(x=0, linestyle='--', color='black')
        ax1.set_xlabel('Time (s)')
        ax1.set_xlim(aligned_timestamps[0], aligned_timestamps[-1])

        if title:
            plt.suptitle(title)

        return fig
