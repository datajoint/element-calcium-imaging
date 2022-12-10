import numpy as np


def calculate_dff(fs, q=5):
    """
    Calculates df/f.

    Args:
        fs (np.array): Fluorescence trace.
        q (float): Quantile (e.g. 5)

    Returns:
        dff (np.array): df over f.
    """
    f0 = np.percentile(fs, q, -1)
    return (fs - f0) / f0


def combine_trials(fissa_output, file="result", comp=0):
    """
    Fissa stores the traces in a splitted manner. This function combines the results.

    Args:
        fissa_output (npz object): fissa output
        file (str): file in the npz object.
        comp (int): signal component. 0 is the cell signal whereas the rest is the background signals.

    Returns:
        traces (np.array): traces for each cell [cell_id, time].
    """

    ntrials = fissa_output[file].shape[1]  # number of imaging (e.g. tiff) files

    traces = []
    for cell in fissa_output[file]:
        traces.append(
            np.concatenate([x[comp] for x in cell[: ntrials - 1]] + [cell[-1][0]])
        )

    return np.array(traces)


def calculate_zscore(trace, n_quiet_frames=153):
    """
    Calculate z score using a given quiet activity period.

    Note: The baseline is defined from the scan's first 10 s, which translates to
        the first 153 frames given the fps = 65 ms / frames.
        n_quiet_frames: 10s / (65 ms/frames) = 152.43 ~ 153.

    Args:
        trace (np.array): Trace whose z score to be calculated.
        n_quiet_frames (int): Number of the frames starting from 0 to define a quite period.

    Returns:
        z score (np.array): z score of the given trace.
    """
    mean_dff_quiet = trace[:n_quiet_frames].mean()
    std_dff_quiet = trace[:n_quiet_frames].std()
    return (trace - mean_dff_quiet) / std_dff_quiet
