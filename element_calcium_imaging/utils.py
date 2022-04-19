import nd2
import fissa
import numpy as np
from suite2p.registration.register import shift_frames
from element_calcium_imaging.scan import *
from element_calcium_imaging.imaging_no_curation2 import *


def shift_frames_with_suite2p(key, suite2p_dataset):
    file = find_full_path(
        get_imaging_root_data_dir(),
        (Fluorescence * ScanInfo.ScanFile & key).fetch("file_path", limit=1)[0],
    ).as_posix()
    frames = nd2.imread(file)
    xoff = suite2p_dataset.planes[0].ops["xoff"]  # (MotionCorrection.RigidMotionCorrection & key).fetch1("x_shifts")
    yoff = suite2p_dataset.planes[0].ops["yoff"]  # (MotionCorrection.RigidMotionCorrection & key).fetch1("y_shifts")
    xoff1 = suite2p_dataset.planes[0].ops[
        "xoff1"
    ]  # np.expand_dims((MotionCorrection.Block & key).fetch1("x_shifts"), 1)
    yoff1 = suite2p_dataset.planes[0].ops[
        "yoff1"
    ]  # np.expand_dims((MotionCorrection.Block & key).fetch1("y_shifts"), 1)
    ops = suite2p_dataset.planes[0].ops

    return shift_frames(frames, xoff, yoff, xoff1, yoff1, ops)


def custom_activity(self, key):
    processing_method, suite2p_dataset = get_loader_result(key, ProcessingTask)

    # Apply motion correction
    registered_frames = shift_frames_with_suite2p(key, suite2p_dataset)

    fissa_params = (ActivityExtractionParamSet & key).fetch1("params")

    # TODO: Do the registration -- DONE!
    # reg_img_dir = find_full_path(
    #    get_imaging_root_data_dir(),
    #    "subject0/session0/scan_0/suite2p/plane0/reg_tif",
    # ).as_posix()

    output_folder = (ProcessingTask & key).fetch("processing_output_dir", limit=1)[0]
    output_folder = (find_full_path(get_imaging_root_data_dir(), output_folder) / "FISSA_Suite2p").as_posix()

    # if the folder doesn't exist create it

    Ly, Lx = (MotionCorrection.Summary & key).fetch("average_image", limit=1)[0].shape

    stat = suite2p_dataset.planes[0].stat
    iscell = suite2p_dataset.planes[0].iscell
    ncells = len(Segmentation.Mask & key)
    cell_ids = np.arange(ncells)
    cell_ids = cell_ids[iscell == 1]

    num_rois = len(cell_ids)
    rois = [np.zeros((Ly, Lx), dtype=bool) for n in range(num_rois)]

    for i, n in enumerate(cell_ids):
        # i is the position in cell_ids, and n is the actual cell number
        ypix = stat[n]["ypix"][~stat[n]["overlap"]]
        xpix = stat[n]["xpix"][~stat[n]["overlap"]]
        rois[i][ypix, xpix] = 1

    experiment = fissa.Experiment(registered_frames, [rois[:ncells]], output_folder, **fissa_params["init"])
    experiment.separate(**fissa_params["exec"])

    cell1_trace1 = experiment.result[0, 0][0]

    q = 10
    perc = np.percentile(cell1_trace1, q=q)
    F0 = cell1_trace1[cell1_trace1 < perc].median()

    # fps = (scan.ScanInfo & key).fetch("fps", limit=1)[0]

    spikes = "?"  # TODO

    self.insert1(key)
    self.Trace.insert(spikes)


def grab_traces(file="separated.npy"):
    sep = np.load(file, allow_pickle=True)
    return np.array([sep[3, x][0][0] for x in range(sep.shape[1])])  # cell, trace


def deltaf_f(fs, q=5):
    """
    fs: np.array(cell, trace)
        traces from all cells
    q: float
        quantile (e.g. 10)
    """
    f0s = np.percentile(fs, q, -1)
    return ((fs.T - f0s) / f0s).T


def filter_cells(dff0, pct=0.05):
    n_nonzeros = np.count_nonzero(dff0, -1)
    return dff0[n_nonzeros > dff0.shape[1] * 0.05]


def zscore(dff, n_quiet_frames=153):
    """
    n_quiet_frames: 10s / (65 ms/frames) = 152.43 ~ 153 frames
    Z_dff0(t) = (dff0(t) - mean(dff0_quiet)) / std(dff0_quiet)
    """
    mean_dff_quiet = dff[:, :n_quiet_frames].mean(-1)
    std_dff_quiet = dff[:, :n_quiet_frames].std(-1)
    return ((dff.T - mean_dff_quiet) / std_dff_quiet).T


sep = np.load("separated.npy", allow_pickle=True)
fs = grab_traces()
dff = deltaf_f(fs)
zs = zscore(dff)

# window_width: 5s / (65.6 frames/s) = 76.21 ~ 77 frames
# zs[zs<]

window_width = 77
detection_factor = 4
v = np.lib.stride_tricks.sliding_window_view(zs, window_width, -1)  # (146, 4496, 77)
