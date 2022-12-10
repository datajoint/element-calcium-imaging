import numpy as np


def calculate_dff(fs, q=5):
    """
    fs: np.array(trace)
        fluorescence trace
    q: float
        quantile (e.g. 5)
    """
    f0 = np.percentile(fs, q, -1)
    return (fs - f0) / f0


def combine_trials(fissa_output, file="result", comp=0):
    """
    Inputs
    ------
    fissa_output: npz object
        fissa output
    file: str
        file in the npz object
    comp: int
        signal component. 0 is the cell signal whereas the rest is the background signals
    Output
    ------
    traces: np.array
        traces for each cell [cell, time]
    """

    ntrials = fissa_output[file].shape[1]  # number of imaging (e.g. tiff) files

    traces = []
    for cell in fissa_output[file]:
        traces.append(
            np.concatenate([x[comp] for x in cell[: ntrials - 1]] + [cell[-1][0]])
        )

    return np.array(traces)


def calculate_zscore(dff, n_quiet_frames=153):
    """
    Client defines the baseline from the first 10 seconds, which corresponds to the first 153 frames.
    n_quiet_frames: 10s / (65 ms/frames) = 152.43 ~ 153 frames
    Z_dff0(t) = (dff0(t) - mean(dff0_quiet)) / std(dff0_quiet)
    """
    mean_dff_quiet = dff[:n_quiet_frames].mean()
    std_dff_quiet = dff[:n_quiet_frames].std()
    return (dff - mean_dff_quiet) / std_dff_quiet


# This was in the matlab codes, will be used later.
def filter_cells(dff, pct=0.05):
    n_nonzeros = np.count_nonzero(dff, -1)
    return dff[n_nonzeros > dff.shape[1] * 0.05]
