import importlib
import inspect

import datajoint as dj
import numpy as np

schema = dj.schema()

_linking_module = None


def activate(
    schema_name, *, create_schema=True, create_tables=True, linking_module=None
):
    """Activate this schema.

    Args:
        schema_name (str): Schema name on the database server to activate the `subject`
            element.
        create_schema (bool): When True (default), create schema in the database if it
            does not yet exist.
        create_tables (bool): When True (default), create tables in the database if they
            do not yet exist.
        linking_module (str): A module name or a module containing the required
            dependencies to activate the `subject` element: Upstream schema: scan,
            session, trial.
    """
    if isinstance(linking_module, str):
        linking_module = importlib.import_module(linking_module)
    assert inspect.ismodule(linking_module), (
        "The argument 'dependency' must " + "be a module's name or a module"
    )

    global _linking_module
    _linking_module = linking_module

    schema.activate(
        schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        add_objects=linking_module.__dict__,
    )


@schema
class ActivityAlignmentCondition(dj.Manual):
    """Activity alignment condition.

    Attributes:
        imaging.Activity (foreign key): Primary key from imaging.Activity.
        event.AlignmentEvent (foreign key): Primary key from event.AlignmentEvent.
        trial_condition (str): User-friendly name of condition.
        condition_description (str). Optional. Description. Default is ''.
        bin_size (float): bin-size (in second) used to compute the PSTH,
    """

    definition = """
    -> imaging.Activity
    -> event.AlignmentEvent
    trial_condition: varchar(128) # user-friendly name of condition
    ---
    condition_description='': varchar(1000)
    bin_size=0.04: float # bin-size (in second) used to compute the PSTH
    """

    class Trial(dj.Part):
        """Trial

        Attributes:
            ActivityAlignmentCondition (foreign key): Primary key from
                ActivityAlignmentCondition.
            trial.Trial: Primary key from trial.Trial.
        """

        definition = """  # Trials (or subset) to compute event-aligned activity
        -> master
        -> trial.Trial
        """


@schema
class ActivityAlignment(dj.Computed):
    """
    Attributes:
        ActivityAlignmentCondition (foreign key): Primary key from
            ActivityAlignmentCondition.
        aligned_timestamps (longblob): Aligned timestamps.
    """

    definition = """
    -> ActivityAlignmentCondition
    ---
    aligned_timestamps: longblob
    """

    class AlignedTrialActivity(dj.Part):
        """Aligned trial activity.

        Attributes:
            ActivityAlignment (foreign key): Primary key from ActivityAlignment.
            imaging.Activity.Trace (foreign key): Primary key from
                imaging.Activity.Trace.
            ActivityAlignmentCondition.Trial (foreign key): Primary key from
                ActivityAlignmentCondition.Trial.
            aligned_trace (longblob): Calcium activity aligned to the event time (s).
        """

        definition = """
        -> master
        -> imaging.Activity.Trace
        -> ActivityAlignmentCondition.Trial
        ---
        aligned_trace: longblob  # (s) Calcium activity aligned to the event time
        """

    def make(self, key):
        sess_time, scan_time, nframes, frame_rate = (
            _linking_module.scan.ScanInfo * _linking_module.session.Session & key
        ).fetch1("session_datetime", "scan_datetime", "nframes", "fps")

        trialized_event_times = (
            _linking_module.trial.get_trialized_alignment_event_times(
                key,
                _linking_module.trial.Trial & (ActivityAlignmentCondition.Trial & key),
            )
        )

        min_limit = (trialized_event_times.event - trialized_event_times.start).max()
        max_limit = (trialized_event_times.end - trialized_event_times.event).max()

        aligned_timestamps = np.arange(-min_limit, max_limit, 1 / frame_rate)
        nsamples = len(aligned_timestamps)

        trace_keys, activity_traces = (
            _linking_module.imaging.Activity.Trace & key
        ).fetch("KEY", "activity_trace", order_by="mask")
        activity_traces = np.vstack(activity_traces)

        aligned_trial_activities = []
        for _, r in trialized_event_times.iterrows():
            if r.event is None or np.isnan(r.event):
                continue
            alignment_start_idx = int((r.event - min_limit) * frame_rate)
            roi_aligned_activities = activity_traces[
                :, alignment_start_idx : (alignment_start_idx + nsamples)
            ]
            if roi_aligned_activities.shape[-1] != nsamples:
                shape_diff = nsamples - roi_aligned_activities.shape[-1]
                roi_aligned_activities = np.pad(
                    roi_aligned_activities,
                    ((0, 0), (0, shape_diff)),
                    mode="constant",
                    constant_values=np.nan,
                )

            aligned_trial_activities.extend(
                [
                    {**key, **r.trial_key, **trace_key, "aligned_trace": aligned_trace}
                    for trace_key, aligned_trace in zip(
                        trace_keys, roi_aligned_activities
                    )
                ]
            )

        self.insert1({**key, "aligned_timestamps": aligned_timestamps})
        self.AlignedTrialActivity.insert(aligned_trial_activities)

    def plot_aligned_activities(self, key, roi, axs=None, title=None):
        """Plot event-aligned activities for selected trials, and trial-averaged
            activity (e.g. dF/F, neuropil-corrected dF/F, Calcium events, etc.).

        Args:
            key (dict): key of ActivityAlignment master table
            roi (int): imaging segmentation mask
            axs (matplotlib.ax): optional definition of axes for plot.
                Default is plt.subplots(2, 1, figsize=(12, 8))
            title (str): Optional title label

        Returns:
            fig (matplotlib.pyplot.figure): Figure of the event aligned activities.
        """
        import matplotlib.pyplot as plt

        fig = None
        if axs is None:
            fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(12, 8))
        else:
            ax0, ax1 = axs

        aligned_timestamps = (self & key).fetch1("aligned_timestamps")
        trial_ids, aligned_spikes = (
            self.AlignedTrialActivity & key & {"mask": roi}
        ).fetch("trial_id", "aligned_trace", order_by="trial_id")

        aligned_spikes = np.vstack(aligned_spikes)

        ax0.imshow(
            aligned_spikes,
            cmap="inferno",
            interpolation="nearest",
            aspect="auto",
            extent=(
                aligned_timestamps[0],
                aligned_timestamps[-1],
                0,
                aligned_spikes.shape[0],
            ),
        )
        ax0.axvline(x=0, linestyle="--", color="white")
        ax0.set_axis_off()

        ax1.plot(aligned_timestamps, np.nanmean(aligned_spikes, axis=0))
        ax1.axvline(x=0, linestyle="--", color="black")
        ax1.set_xlabel("Time (s)")
        ax1.set_xlim(aligned_timestamps[0], aligned_timestamps[-1])

        if title:
            plt.suptitle(title)

        return fig
