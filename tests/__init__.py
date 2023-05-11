"""
run all: python -m pytest -sv --cov-report term-missing --cov=workflow_calcium_imaging --sw -p no:warnings tests/
run one: python -m pytest -sv --cov-report term-missing --cov=workflow_calcium_imaging --sw -p no:warnings --pdb tests/module_name.py -k function_name
"""

import os
import pathlib
import sys
from contextlib import nullcontext

import datajoint as dj
import numpy as np
import pandas as pd
import pytest
from element_interface.utils import find_full_path, find_root_directory

# ------------------- SOME CONSTANTS -------------------

_tear_down = False

test_user_data_dir = pathlib.Path("./tests/user_data")
test_user_data_dir.mkdir(exist_ok=True)

sessions_dirs = [
    "subject0/session1",
    "subject1/20200609_170519",
    "subject1/20200609_171646",
    "subject2/20200420_1843959",
    "subject3/210107_run00_orientation_8dir",
]

is_multi_scan_processing = False

verbose = False

logger = dj.logger

# ------------------ GENERAL FUCNTION ------------------


class QuietStdOut:
    """If verbose set to false, used to quiet tear_down table.delete prints"""

    def __enter__(self):
        logger.setLevel("ERROR")
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.setLevel("INFO")
        sys.stdout.close()
        sys.stdout = self._original_stdout


verbose_context = nullcontext() if verbose else QuietStdOut()

# ------------------- FIXTURES -------------------


@pytest.fixture
def pipeline():
    with verbose_context:
        print("\n")
        from workflow_calcium_imaging import paths, pipeline

    global is_multi_scan_processing
    is_multi_scan_processing = (
        "processing_task_id" in pipeline.imaging.ProcessingTask.heading.names
    )

    yield {
        "subject": pipeline.subject,
        "lab": pipeline.lab,
        "imaging": pipeline.imaging,
        "scan": pipeline.scan,
        "session": pipeline.session,
        "Equipment": pipeline.Equipment,
        "get_imaging_root_data_dir": paths.get_imaging_root_data_dir,
    }

    if _tear_down:
        with verbose_context:
            pipeline.subject.Subject.delete()


@pytest.fixture
def subjects_csv():
    """Create a 'subjects.csv' file"""
    input_subjects = pd.DataFrame(
        columns=["subject", "sex", "subject_birth_date", "subject_description"]
    )
    input_subjects.subject = ["subject0", "subject1", "subject2", "subject3"]
    input_subjects.sex = ["M", "F", "M", "F"]
    input_subjects.subject_birth_date = [
        "2020-01-01 00:00:01",
        "2020-01-01 00:00:01",
        "2020-01-01 00:00:01",
        "2020-01-01 00:00:01",
    ]
    input_subjects.subject_description = ["mika_animal", "91760", "90853", "sbx-JC015"]
    input_subjects = input_subjects.set_index("subject")

    subjects_csv_path = pathlib.Path("./tests/user_data/subjects.csv")
    input_subjects.to_csv(subjects_csv_path)  # write csv file

    yield input_subjects, subjects_csv_path

    if _tear_down:
        with verbose_context:
            subjects_csv_path.unlink()  # delete csv file after use


@pytest.fixture
def ingest_subjects(pipeline, subjects_csv):
    from workflow_calcium_imaging.ingest import ingest_subjects

    _, subjects_csv_path = subjects_csv
    with verbose_context:
        ingest_subjects(subjects_csv_path)
    return


@pytest.fixture
def sessions_csv(test_data, pipeline):
    """Create a 'sessions.csv' file"""
    root_dirs = pipeline["get_imaging_root_data_dir"]

    input_sessions = pd.DataFrame(columns=["subject", "session_dir"])
    input_sessions.subject = [
        "subject0",
        "subject1",
        "subject1",
        "subject2",
        "subject3",
    ]
    input_sessions.session_dir = [
        find_full_path(root_dirs(), sess_dir) for sess_dir in sessions_dirs
    ]
    input_sessions = input_sessions.set_index("subject")

    sessions_csv_path = pathlib.Path("./tests/user_data/sessions.csv")
    input_sessions.to_csv(sessions_csv_path)  # write csv file

    yield input_sessions, sessions_csv_path

    if _tear_down:
        with verbose_context:
            sessions_csv_path.unlink()  # delete csv file after use


@pytest.fixture
def ingest_sessions(ingest_subjects, sessions_csv):
    from workflow_calcium_imaging.ingest import ingest_sessions

    _, sessions_csv_path = sessions_csv
    with verbose_context:
        ingest_sessions(sessions_csv_path)
    return


@pytest.fixture
def testdata_paths():
    return {
        "scanimage_2d": "subject1/20200609_171646",
        "scanimage_3d": "subject2/20200420_1843959",
        "scanimage_multiroi": "subject0/session1",
        "scanbox_3d": "subject3/210107_run00_orientation_8dir",
        "suite2p_2d": "subject1/20200609_171646/suite2p",
        "suite2p_3d_a": "subject2/20200420_1843959/suite2p",
        "suite2p_3d_b": "subject3/210107_run00_orientation_8dir/suite2p",
        "caiman_2d": "subject1/20200609_170519/caiman",
    }


@pytest.fixture
def suite2p_paramset(pipeline):
    imaging = pipeline["imaging"]

    params_suite2p = {
        "look_one_level_down": 0.0,
        "fast_disk": [],
        "delete_bin": False,
        "mesoscan": False,
        "h5py": [],
        "h5py_key": "data",
        "save_path0": [],
        "subfolders": [],
        "nplanes": 1,
        "nchannels": 1,
        "functional_chan": 1,
        "tau": 1.0,
        "fs": 10.0,
        "force_sktiff": False,
        "preclassify": 0.0,
        "save_mat": False,
        "combined": True,
        "aspect": 1.0,
        "do_bidiphase": False,
        "bidiphase": 0.0,
        "do_registration": True,
        "keep_movie_raw": False,
        "nimg_init": 300,
        "batch_size": 500,
        "maxregshift": 0.1,
        "align_by_chan": 1,
        "reg_tif": False,
        "reg_tif_chan2": False,
        "subpixel": 10,
        "smooth_sigma": 1.15,
        "th_badframes": 1.0,
        "pad_fft": False,
        "nonrigid": True,
        "block_size": [128, 128],
        "snr_thresh": 1.2,
        "maxregshiftNR": 5.0,
        "1Preg": False,
        "spatial_hp": 50.0,
        "pre_smooth": 2.0,
        "spatial_taper": 50.0,
        "roidetect": True,
        "sparse_mode": False,
        "diameter": 12,
        "spatial_scale": 0,
        "connected": True,
        "nbinned": 5000,
        "max_iterations": 20,
        "threshold_scaling": 1.0,
        "max_overlap": 0.75,
        "high_pass": 100.0,
        "inner_neuropil_radius": 2,
        "min_neuropil_pixels": 350,
        "allow_overlap": False,
        "chan2_thres": 0.65,
        "baseline": "maximin",
        "win_baseline": 60.0,
        "sig_baseline": 10.0,
        "prctile_baseline": 8.0,
        "neucoeff": 0.7,
        "xrange": np.array([0, 0]),
        "yrange": np.array([0, 0]),
    }

    # doing the insert here as well, since most of the test will require this paramset inserted
    imaging.ProcessingParamSet.insert_new_params(
        "suite2p",
        0,
        "Calcium imaging analysis with" " Suite2p using default Suite2p parameters",
        params_suite2p,
    )

    yield params_suite2p

    if _tear_down:
        with verbose_context:
            (imaging.ProcessingParamSet & "paramset_idx = 0").delete()


@pytest.fixture
def caiman2D_paramset(pipeline):
    imaging = pipeline["imaging"]

    params_caiman_2d = {
        "fnames": None,
        "dims": None,
        "decay_time": 0.4,
        "dxy": (1, 1),
        "var_name_hdf5": "mov",
        "last_commit": "GITW-a99c03c9cb221e802ec71aacfb988257810c8c4a",
        "mmap_F": None,
        "mmap_C": None,
        "block_size_spat": 5000,
        "dist": 3,
        "expandCore": np.array(
            [
                [0, 0, 1, 0, 0],
                [0, 1, 1, 1, 0],
                [1, 1, 1, 1, 1],
                [0, 1, 1, 1, 0],
                [0, 0, 1, 0, 0],
            ],
            dtype="int32",
        ),
        "extract_cc": True,
        "maxthr": 0.1,
        "medw": None,
        "method_exp": "dilate",
        "method_ls": "lasso_lars",
        "n_pixels_per_process": None,
        "nb": 1,
        "normalize_yyt_one": True,
        "nrgthr": 0.9999,
        "num_blocks_per_run_spat": 20,
        "se": np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype="uint8"),
        "ss": np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype="uint8"),
        "thr_method": "nrg",
        "update_background_components": True,
        "ITER": 2,
        "bas_nonneg": False,
        "block_size_temp": 5000,
        "fudge_factor": 0.96,
        "lags": 5,
        "optimize_g": False,
        "memory_efficient": False,
        "method_deconvolution": "oasis",
        "noise_method": "mean",
        "noise_range": [0.25, 0.5],
        "num_blocks_per_run_temp": 20,
        "p": 2,
        "s_min": None,
        "solvers": ["ECOS", "SCS"],
        "verbosity": False,
        "K": 30,
        "SC_kernel": "heat",
        "SC_sigma": 1,
        "SC_thr": 0,
        "SC_normalize": True,
        "SC_use_NN": False,
        "SC_nnn": 20,
        "alpha_snmf": 100,
        "center_psf": False,
        "gSig": [5, 5],
        "gSiz": (11, 11),
        "init_iter": 2,
        "kernel": None,
        "lambda_gnmf": 1,
        "maxIter": 5,
        "max_iter_snmf": 500,
        "method_init": "greedy_roi",
        "min_corr": 0.85,
        "min_pnr": 20,
        "nIter": 5,
        "normalize_init": True,
        "options_local_NMF": None,
        "perc_baseline_snmf": 20,
        "ring_size_factor": 1.5,
        "rolling_length": 100,
        "rolling_sum": True,
        "seed_method": "auto",
        "sigma_smooth_snmf": (0.5, 0.5, 0.5),
        "ssub": 2,
        "ssub_B": 2,
        "tsub": 2,
        "check_nan": True,
        "compute_g": False,
        "include_noise": False,
        "max_num_samples_fft": 3072,
        "pixels": None,
        "sn": None,
        "border_pix": 0,
        "del_duplicates": False,
        "in_memory": True,
        "low_rank_background": True,
        "memory_fact": 1,
        "n_processes": 1,
        "nb_patch": 1,
        "only_init": True,
        "p_patch": 0,
        "remove_very_bad_comps": False,
        "rf": None,
        "skip_refinement": False,
        "p_ssub": 2,
        "stride": None,
        "p_tsub": 2,
        "N_samples_exceptionality": 12,
        "batch_update_suff_stat": False,
        "dist_shape_update": False,
        "ds_factor": 1,
        "epochs": 1,
        "expected_comps": 500,
        "full_XXt": False,
        "init_batch": 200,
        "init_method": "bare",
        "iters_shape": 5,
        "max_comp_update_shape": np.inf,
        "max_num_added": 5,
        "max_shifts_online": 10,
        "min_SNR": 2.5,
        "min_num_trial": 5,
        "minibatch_shape": 100,
        "minibatch_suff_stat": 5,
        "motion_correct": True,
        "movie_name_online": "online_movie.mp4",
        "normalize": False,
        "n_refit": 0,
        "num_times_comp_updated": np.inf,
        "opencv_codec": "H264",
        "path_to_model": None,
        "ring_CNN": False,
        "rval_thr": 0.8,
        "save_online_movie": False,
        "show_movie": False,
        "simultaneously": False,
        "sniper_mode": False,
        "stop_detection": False,
        "test_both": False,
        "thresh_CNN_noisy": 0.5,
        "thresh_fitness_delta": -50,
        "thresh_fitness_raw": -60.97977932734429,
        "thresh_overlap": 0.5,
        "update_freq": 200,
        "update_num_comps": True,
        "use_corr_img": False,
        "use_dense": True,
        "use_peak_max": True,
        "W_update_factor": 1,
        "SNR_lowest": 0.5,
        "cnn_lowest": 0.1,
        "gSig_range": None,
        "min_cnn_thr": 0.9,
        "rval_lowest": -1,
        "use_cnn": True,
        "use_ecc": False,
        "max_ecc": 3,
        "do_merge": True,
        "merge_thr": 0.8,
        "merge_parallel": False,
        "max_merge_area": None,
        "border_nan": "copy",
        "gSig_filt": None,
        "is3D": False,
        "max_deviation_rigid": 3,
        "max_shifts": (6, 6),
        "min_mov": None,
        "niter_rig": 1,
        "nonneg_movie": True,
        "num_frames_split": 80,
        "num_splits_to_process_els": None,
        "num_splits_to_process_rig": None,
        "overlaps": (32, 32),
        "pw_rigid": False,
        "shifts_opencv": True,
        "splits_els": 14,
        "splits_rig": 14,
        "strides": (96, 96),
        "upsample_factor_grid": 4,
        "use_cuda": False,
        "n_channels": 2,
        "use_bias": False,
        "use_add": False,
        "pct": 0.01,
        "patience": 3,
        "max_epochs": 100,
        "width": 5,
        "loss_fn": "pct",
        "lr": 0.001,
        "lr_scheduler": None,
        "remove_activity": False,
        "reuse_model": False,
    }

    imaging.ProcessingParamSet.insert_new_params(
        "caiman",
        1,
        "Calcium imaging analysis with"
        " CaImAn using default CaImAn parameters for 2d planar images",
        params_caiman_2d,
    )

    yield params_caiman_2d

    if _tear_down:
        with verbose_context:
            (imaging.ProcessingParamSet & "paramset_idx = 1").delete()


@pytest.fixture
def caiman3D_paramset(pipeline):
    imaging = pipeline["imaging"]

    params_caiman_3d = {
        "fnames": None,
        "dims": None,
        "decay_time": 0.4,
        "dxy": (1, 1),
        "var_name_hdf5": "mov",
        "last_commit": "GITW-a99c03c9cb221e802ec71aacfb988257810c8c4a",
        "mmap_F": None,
        "mmap_C": None,
        "block_size_spat": 5000,
        "dist": 3,
        "expandCore": np.array(
            [
                [0, 0, 1, 0, 0],
                [0, 1, 1, 1, 0],
                [1, 1, 1, 1, 1],
                [0, 1, 1, 1, 0],
                [0, 0, 1, 0, 0],
            ],
            dtype="int32",
        ),
        "extract_cc": True,
        "maxthr": 0.1,
        "medw": None,
        "method_exp": "dilate",
        "method_ls": "lasso_lars",
        "n_pixels_per_process": None,
        "nb": 1,
        "normalize_yyt_one": True,
        "nrgthr": 0.9999,
        "num_blocks_per_run_spat": 20,
        "se": np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype="uint8"),
        "ss": np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype="uint8"),
        "thr_method": "nrg",
        "update_background_components": True,
        "ITER": 2,
        "bas_nonneg": False,
        "block_size_temp": 5000,
        "fudge_factor": 0.96,
        "lags": 5,
        "optimize_g": False,
        "memory_efficient": False,
        "method_deconvolution": "oasis",
        "noise_method": "mean",
        "noise_range": [0.25, 0.5],
        "num_blocks_per_run_temp": 20,
        "p": 2,
        "s_min": None,
        "solvers": ["ECOS", "SCS"],
        "verbosity": False,
        "K": 30,
        "SC_kernel": "heat",
        "SC_sigma": 1,
        "SC_thr": 0,
        "SC_normalize": True,
        "SC_use_NN": False,
        "SC_nnn": 20,
        "alpha_snmf": 100,
        "center_psf": False,
        "gSig": (5, 5, 1),
        "gSiz": (11, 11),
        "init_iter": 2,
        "kernel": None,
        "lambda_gnmf": 1,
        "maxIter": 5,
        "max_iter_snmf": 500,
        "method_init": "greedy_roi",
        "min_corr": 0.85,
        "min_pnr": 20,
        "nIter": 5,
        "normalize_init": True,
        "options_local_NMF": None,
        "perc_baseline_snmf": 20,
        "ring_size_factor": 1.5,
        "rolling_length": 100,
        "rolling_sum": True,
        "seed_method": "auto",
        "sigma_smooth_snmf": (0.5, 0.5, 0.5),
        "ssub": 2,
        "ssub_B": 2,
        "tsub": 2,
        "check_nan": True,
        "compute_g": False,
        "include_noise": False,
        "max_num_samples_fft": 3072,
        "pixels": None,
        "sn": None,
        "border_pix": 0,
        "del_duplicates": False,
        "in_memory": True,
        "low_rank_background": True,
        "memory_fact": 1,
        "n_processes": 1,
        "nb_patch": 1,
        "only_init": True,
        "p_patch": 0,
        "remove_very_bad_comps": False,
        "rf": None,
        "skip_refinement": False,
        "p_ssub": 2,
        "stride": None,
        "p_tsub": 2,
        "N_samples_exceptionality": 12,
        "batch_update_suff_stat": False,
        "dist_shape_update": False,
        "ds_factor": 1,
        "epochs": 1,
        "expected_comps": 500,
        "full_XXt": False,
        "init_batch": 200,
        "init_method": "bare",
        "iters_shape": 5,
        "max_comp_update_shape": np.inf,
        "max_num_added": 5,
        "max_shifts_online": 10,
        "min_SNR": 2.5,
        "min_num_trial": 5,
        "minibatch_shape": 100,
        "minibatch_suff_stat": 5,
        "motion_correct": True,
        "movie_name_online": "online_movie.mp4",
        "normalize": False,
        "n_refit": 0,
        "num_times_comp_updated": np.inf,
        "opencv_codec": "H264",
        "path_to_model": None,
        "ring_CNN": False,
        "rval_thr": 0.8,
        "save_online_movie": False,
        "show_movie": False,
        "simultaneously": False,
        "sniper_mode": False,
        "stop_detection": False,
        "test_both": False,
        "thresh_CNN_noisy": 0.5,
        "thresh_fitness_delta": -50,
        "thresh_fitness_raw": -60.97977932734429,
        "thresh_overlap": 0.5,
        "update_freq": 200,
        "update_num_comps": True,
        "use_corr_img": False,
        "use_dense": True,
        "use_peak_max": True,
        "W_update_factor": 1,
        "SNR_lowest": 0.5,
        "cnn_lowest": 0.1,
        "gSig_range": None,
        "min_cnn_thr": 0.9,
        "rval_lowest": -1,
        "use_cnn": False,
        "use_ecc": False,
        "max_ecc": 3,
        "do_merge": True,
        "merge_thr": 0.8,
        "merge_parallel": False,
        "max_merge_area": None,
        "border_nan": "copy",
        "gSig_filt": None,
        "is3D": False,
        "max_deviation_rigid": 3,
        "max_shifts": (6, 6, 1),
        "min_mov": None,
        "niter_rig": 1,
        "nonneg_movie": True,
        "num_frames_split": 80,
        "num_splits_to_process_els": None,
        "num_splits_to_process_rig": None,
        "overlaps": (32, 32, 1),
        "pw_rigid": False,
        "shifts_opencv": True,
        "splits_els": 14,
        "splits_rig": 14,
        "strides": (96, 96, 1),
        "upsample_factor_grid": 4,
        "use_cuda": False,
        "n_channels": 2,
        "use_bias": False,
        "use_add": False,
        "pct": 0.01,
        "patience": 3,
        "max_epochs": 100,
        "width": 5,
        "loss_fn": "pct",
        "lr": 0.001,
        "lr_scheduler": None,
        "remove_activity": False,
        "reuse_model": False,
    }

    imaging.ProcessingParamSet.insert_new_params(
        "caiman",
        2,
        "Calcium imaging analysis with"
        " CaImAn using default CaImAn parameters for 3d volumetric images",
        params_caiman_3d,
    )

    yield params_caiman_3d

    if _tear_down:
        with verbose_context:
            (imaging.ProcessingParamSet & "paramset_idx = 2").delete()


@pytest.fixture
def scan_info(pipeline, ingest_sessions):
    scan = pipeline["scan"]

    scan.ScanInfo.populate()

    yield

    if _tear_down:
        with verbose_context:
            scan.ScanInfo.delete()


@pytest.fixture
def processing_tasks(
    pipeline, suite2p_paramset, caiman2D_paramset, caiman3D_paramset, scan_info
):
    global is_multi_scan_processing

    imaging = pipeline["imaging"]
    scan = pipeline["scan"]
    session = pipeline["session"]
    get_imaging_root_data_dir = pipeline["get_imaging_root_data_dir"]
    root_dirs = get_imaging_root_data_dir()

    if is_multi_scan_processing:
        for session_key in (
            session.Session & scan.ScanInfo - imaging.ProcessingTask
        ).fetch("KEY"):
            scan_file = find_full_path(
                root_dirs, (scan.ScanInfo.ScanFile & session_key).fetch("file_path")[0]
            )
            recording_dir = scan_file.parent
            # suite2p
            suite2p_dir = recording_dir / "suite2p"
            if suite2p_dir.exists():
                processing_key = {
                    **session_key,
                    "paramset_idx": 0,
                    "processing_task_id": 0,
                }
                imaging.ProcessingTask.insert1(
                    {**processing_key, "processing_output_dir": suite2p_dir.as_posix()}
                )
                imaging.ProcessingTask.Scan.insert(
                    {**processing_key, **scan_key}
                    for scan_key in (scan.Scan & session_key).fetch("KEY")
                )
            # caiman
            caiman_dir = recording_dir / "caiman"
            if caiman_dir.exists():
                is_3D = (scan.ScanInfo & session_key).fetch("ndepths")[0] > 1
                processing_key = {
                    **session_key,
                    "paramset_idx": 1 if not is_3D else 2,
                    "processing_task_id": 0,
                }
                imaging.ProcessingTask.insert1(
                    {**processing_key, "processing_output_dir": caiman_dir.as_posix()}
                )
                imaging.ProcessingTask.Scan.insert(
                    {**processing_key, **scan_key}
                    for scan_key in (scan.Scan & session_key).fetch("KEY")
                )
    else:
        for scan_key in (scan.Scan & scan.ScanInfo - imaging.ProcessingTask).fetch(
            "KEY"
        ):
            scan_file = find_full_path(
                root_dirs, (scan.ScanInfo.ScanFile & scan_key).fetch("file_path")[0]
            )
            recording_dir = scan_file.parent
            # suite2p
            suite2p_dir = recording_dir / "suite2p"
            if suite2p_dir.exists():
                imaging.ProcessingTask.insert1(
                    {
                        **scan_key,
                        "paramset_idx": 0,
                        "processing_output_dir": suite2p_dir.as_posix(),
                    }
                )
            # caiman
            caiman_dir = recording_dir / "caiman"
            if caiman_dir.exists():
                is_3D = (scan.ScanInfo & scan_key).fetch1("ndepths") > 1
                imaging.ProcessingTask.insert1(
                    {
                        **scan_key,
                        "paramset_idx": 1 if not is_3D else 2,
                        "processing_output_dir": caiman_dir.as_posix(),
                    }
                )

    yield

    if _tear_down:
        with verbose_context:
            imaging.ProcessingTask.delete()


@pytest.fixture
def trigger_processing_suite2p_2D(pipeline, suite2p_paramset, scan_info):
    """Triggers suite2p pipeline on subject1 data"""
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]
    get_imaging_root_data_dir = pipeline["get_imaging_root_data_dir"]

    # This is to use 1 tif out of 2 - So do not change this to fetch1("KEY")!!!
    key = (scan.ScanInfo * imaging.ProcessingParamSet & "subject='subject1'").fetch(
        "KEY"
    )[0]
    subj1_fullpath = find_full_path(get_imaging_root_data_dir(), sessions_dirs[1])
    subj1_root = find_root_directory(get_imaging_root_data_dir(), subj1_fullpath)

    newkey = key.copy()
    newkey["session_datetime"] = newkey["session_datetime"].strftime("%Y%m%dT%H%M%S")
    output_dir = "demo/" + "_".join(str(newkey[x]) for x in newkey)
    imaging.ProcessingTask.insert1(
        {**key, "processing_output_dir": output_dir, "task_mode": "trigger"},
        skip_duplicates=not _tear_down,
    )
    try:
        os.makedirs(subj1_root / output_dir)
    except OSError as error:
        print(error)

    with verbose_context:
        imaging.Processing.populate(key)

    yield

    if _tear_down:
        with verbose_context:
            (imaging.ProcessingTask & key).delete()
            (imaging.Processing & key).delete()


@pytest.fixture
def processing(processing_tasks, pipeline):
    imaging = pipeline["imaging"]

    with verbose_context:
        errors = imaging.Processing.populate(suppress_errors=True)
        if errors:
            print(
                f"Populate ERROR: {len(errors)} errors in "
                + f'"imaging.Processing.populate()" - {errors[0][-1]}'
            )

    yield

    if _tear_down:
        with verbose_context:
            imaging.Processing.delete()


@pytest.fixture
def curations(processing, pipeline):
    imaging = pipeline["imaging"]

    with verbose_context:
        for key in (imaging.Processing - imaging.Curation).fetch("KEY"):
            imaging.Curation().create1_from_processing_task(key)

    yield

    if _tear_down:
        with verbose_context:
            imaging.Curation.delete()
