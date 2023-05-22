import shutil
import datetime
import pytest

from . import (
    caiman2D_paramset,
    caiman3D_paramset,
    curations,
    ingest_sessions,
    ingest_subjects,
    pipeline,
    processing,
    processing_tasks,
    scan_info,
    sessions_csv,
    subjects_csv,
    suite2p_paramset,
    testdata_paths,
    trigger_processing_suite2p_2D,
    verbose_context,
)


def test_scan_info_populate_scanimage_2D(testdata_paths, pipeline, scan_info):
    scan = pipeline["scan"]
    rel_path = testdata_paths["scanimage_2d"]
    scan_key = (
        scan.ScanInfo & (scan.ScanInfo.ScanFile & f'file_path LIKE "%{rel_path}%"')
    ).fetch1("KEY")
    nfields, nchannels, ndepths, nframes = (scan.ScanInfo & scan_key).fetch1(
        "nfields", "nchannels", "ndepths", "nframes"
    )

    assert nfields == 1
    assert nchannels == 2
    assert ndepths == 1
    assert nframes == 25000


def test_scan_info_populate_scanimage_3D(testdata_paths, pipeline, scan_info):
    scan = pipeline["scan"]

    rel_path = testdata_paths["scanimage_3d"]
    scan_key = (
        scan.ScanInfo & (scan.ScanInfo.ScanFile & f'file_path LIKE "%{rel_path}%"')
    ).fetch1("KEY")
    nfields, nchannels, ndepths, nframes = (scan.ScanInfo & scan_key).fetch1(
        "nfields", "nchannels", "ndepths", "nframes"
    )

    assert nfields == 3
    assert nchannels == 2
    assert ndepths == 3
    assert nframes == 2000


def test_scan_info_populate_scanimage_multiROI(testdata_paths, pipeline, scan_info):
    scan = pipeline["scan"]

    rel_path = testdata_paths["scanimage_multiroi"]
    scan_key = (
        scan.ScanInfo & (scan.ScanInfo.ScanFile & f'file_path LIKE "%{rel_path}%"')
    ).fetch1("KEY")
    nfields, nchannels, ndepths, nframes, nrois = (scan.ScanInfo & scan_key).fetch1(
        "nfields", "nchannels", "ndepths", "nframes", "nrois"
    )

    assert nfields == 3
    assert nchannels == 1
    assert ndepths == 1
    assert nframes == 12000
    assert nrois == 3


def test_scan_info_populate_scanbox_3D(testdata_paths, pipeline, scan_info):
    scan = pipeline["scan"]
    rel_path = testdata_paths["scanbox_3d"]
    scan_key = (
        scan.ScanInfo & (scan.ScanInfo.ScanFile & f'file_path LIKE "%{rel_path}%"')
    ).fetch1("KEY")
    nfields, nchannels, ndepths, nframes = (scan.ScanInfo & scan_key).fetch1(
        "nfields", "nchannels", "ndepths", "nframes"
    )

    assert nfields == 4
    assert nchannels == 1
    assert ndepths == 4
    assert nframes == 7530


def test_processing_populate(processing, pipeline):
    imaging = pipeline["imaging"]

    assert len(imaging.Processing()) == 5


def test_processing_populate_trigger_suite2p_2D(
    trigger_processing_suite2p_2D, pipeline
):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]
    get_imaging_root_data_dir = pipeline["get_imaging_root_data_dir"]
    assert len(imaging.Processing()) == 1

    from element_interface.suite2p_loader import Suite2p

    # fetch('KEY')[0] is intentional to keep the test short. otherwise there are 2 keys.
    key = (scan.ScanInfo * imaging.ProcessingParamSet & "subject='subject1'").fetch(
        "KEY"
    )[0]
    output_dir = (imaging.ProcessingTask & key).fetch1("processing_output_dir")
    output_dir = imaging.find_full_path(
        get_imaging_root_data_dir(), output_dir
    ).as_posix()

    Suite2p(output_dir)

    shutil.rmtree("/main/test_data/demo")


def test_motion_correction_populate_suite2p_2D(curations, pipeline, testdata_paths):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]

    rel_path = testdata_paths["suite2p_2d"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")

    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "suite2p"

    assert len(imaging.MotionCorrection.Block & curation_key) == 9

    x_shifts = (imaging.MotionCorrection.RigidMotionCorrection & curation_key).fetch1(
        "x_shifts"
    )
    assert len(x_shifts) == (scan.ScanInfo & curation_key).fetch1("nframes")

    ave_img = (imaging.MotionCorrection.Summary & curation_key).fetch1("average_image")
    img_width, img_height = (scan.ScanInfo.Field & curation_key).fetch1(
        "px_width", "px_height"
    )
    assert ave_img.shape == (img_height, img_width)


def test_motion_correction_populate_suite2p_3D(curations, pipeline, testdata_paths):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]
    # test-set A
    rel_path = testdata_paths["suite2p_3d_a"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")
    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "suite2p"

    assert len(imaging.MotionCorrection.Block & curation_key) == 36

    x_shifts = (imaging.MotionCorrection.RigidMotionCorrection & curation_key).fetch1(
        "x_shifts"
    )
    nfields, nframes = (scan.ScanInfo & curation_key).fetch1("nfields", "nframes")
    assert x_shifts.shape == (nfields, nframes)
    # test-set B
    rel_path = testdata_paths["suite2p_3d_b"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")
    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "suite2p"

    assert len(imaging.MotionCorrection.Block & curation_key) == 54

    x_shifts = (imaging.MotionCorrection.RigidMotionCorrection & curation_key).fetch1(
        "x_shifts"
    )
    nfields, nframes = (scan.ScanInfo & curation_key).fetch1("nfields", "nframes")
    assert x_shifts.shape == (nfields, nframes)


def test_motion_correction_populate_caiman_2D(curations, pipeline, testdata_paths):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]

    rel_path = testdata_paths["caiman_2d"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "caiman"

    imaging.MotionCorrection.populate(curation_key)

    x_shifts, y_shifts = (
        imaging.MotionCorrection.RigidMotionCorrection & curation_key
    ).fetch1("x_shifts", "y_shifts")
    assert (
        len(x_shifts)
        == len(y_shifts)
        == (scan.ScanInfo & curation_key).fetch1("nframes")
    )

    ave_img = (imaging.MotionCorrection.Summary & curation_key).fetch1("average_image")
    img_width, img_height = (scan.ScanInfo.Field & curation_key).fetch1(
        "px_width", "px_height"
    )
    assert ave_img.shape == (img_height, img_width)


def test_segmentation_populate_suite2p_2D(curations, pipeline, testdata_paths):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]

    rel_path = testdata_paths["suite2p_2d"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")

    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)
        imaging.Segmentation.populate(curation_key)
        imaging.Fluorescence.populate(curation_key)
        imaging.Activity.populate(curation_key)

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "suite2p"

    assert len(imaging.Segmentation.Mask & curation_key) == 57

    assert (
        len(
            imaging.MaskClassification.MaskType
            & curation_key
            & 'mask_classification_method = "suite2p_default_classifier"'
            & 'mask_type = "soma"'
        )
        == 27
    )

    assert len(imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0") == 57
    assert (
        len(
            imaging.Activity.Trace
            & curation_key
            & "fluo_channel = 0"
            & 'extraction_method = "suite2p_deconvolution"'
        )
        == 57
    )

    nframes = (scan.ScanInfo & curation_key).fetch1("nframes")
    f, fneu = (
        imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0" & "mask = 0"
    ).fetch1("fluorescence", "neuropil_fluorescence")
    assert len(f) == len(fneu) == nframes


def test_segmentation_populate_suite2p_3D(curations, pipeline, testdata_paths):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]

    rel_path = testdata_paths["suite2p_3d_a"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")

    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)
        imaging.Segmentation.populate(curation_key)
        imaging.Fluorescence.populate(curation_key)
        imaging.Activity.populate(curation_key)

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "suite2p"

    assert len(imaging.Segmentation.Mask & curation_key) == 1174

    assert (
        len(
            imaging.MaskClassification.MaskType
            & curation_key
            & 'mask_classification_method = "suite2p_default_classifier"'
            & 'mask_type = "soma"'
        )
        == 432
    )

    assert len(imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0") == 1174
    assert (
        len(
            imaging.Activity.Trace
            & curation_key
            & "fluo_channel = 0"
            & 'extraction_method = "suite2p_deconvolution"'
        )
        == 1174
    )

    nframes = (scan.ScanInfo & curation_key).fetch1("nframes")
    f, fneu = (
        imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0" & "mask = 0"
    ).fetch1("fluorescence", "neuropil_fluorescence")
    assert len(f) == len(fneu) == nframes

    rel_path = testdata_paths["suite2p_3d_b"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")

    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)
        imaging.Segmentation.populate(curation_key)
        imaging.Fluorescence.populate(curation_key)
        imaging.Activity.populate(curation_key)

    assert len(imaging.Segmentation.Mask & curation_key) == 6636

    assert (
        len(
            imaging.MaskClassification.MaskType
            & curation_key
            & 'mask_classification_method = "suite2p_default_classifier"'
            & 'mask_type = "soma"'
        )
        == 2910
    )

    assert len(imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0") == 6636
    assert (
        len(
            imaging.Activity.Trace
            & curation_key
            & "fluo_channel = 0"
            & 'extraction_method = "suite2p_deconvolution"'
        )
        == 6636
    )

    nframes = (scan.ScanInfo & curation_key).fetch1("nframes")
    f, fneu = (
        imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0" & "mask = 0"
    ).fetch1("fluorescence", "neuropil_fluorescence")
    assert len(f) == len(fneu) == nframes


def test_segmentation_populate_caiman_2D(curations, pipeline, testdata_paths):
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]

    rel_path = testdata_paths["caiman_2d"]
    curation_key = (
        imaging.Curation & f'curation_output_dir LIKE "%{rel_path}"'
    ).fetch1("KEY")

    with verbose_context:
        imaging.MotionCorrection.populate(curation_key)
        imaging.Segmentation.populate(curation_key)
        imaging.Fluorescence.populate(curation_key)
        imaging.Activity.populate(curation_key)

    assert (imaging.Curation * imaging.ProcessingParamSet & curation_key).fetch1(
        "processing_method"
    ) == "caiman"

    assert len(imaging.Segmentation.Mask & curation_key) == 30
    assert (
        len(
            imaging.Fluorescence.Trace * imaging.MaskClassification.MaskType
            & curation_key
            & "fluo_channel = 0"
        )
        == 21
    )
    assert (
        len(
            imaging.Activity.Trace * imaging.MaskClassification.MaskType
            & curation_key
            & "fluo_channel = 0"
            & 'extraction_method = "caiman_deconvolution"'
        )
        == 21
    )
    assert (
        len(
            imaging.Activity.Trace * imaging.MaskClassification.MaskType
            & curation_key
            & "fluo_channel = 0"
            & 'extraction_method = "caiman_dff"'
        )
        == 21
    )

    nframes = (scan.ScanInfo & curation_key).fetch1("nframes")
    f = (
        imaging.Fluorescence.Trace & curation_key & "fluo_channel = 0" & "mask = 1"
    ).fetch1("fluorescence")
    assert len(f) == nframes


def test_scan_quality_metrics_populate(pipeline):
    """
    Assert correct values for entries in the scan.ScanQualityMetrics table.
    Run the `demo_prepare.ipynb` notebook, prior to running this test.
    """
    scan = pipeline["scan"]

    key = dict(
        subject="subject1",
        session_datetime=datetime.datetime(2023, 5, 11, 12, 00, 00),
        scan_id=0,
        field_idx=0,
        channel=0,
    )

    with verbose_context:
        scan.ScanQualityMetrics.populate(key)

    scan_metrics = (scan.ScanQualityMetrics.Frames() & key).fetch1()

    assert len(scan_metrics["min_intensity"]) == 3000
    assert len(scan_metrics["mean_intensity"]) == 3000
    assert len(scan_metrics["max_intensity"]) == 3000
    assert len(scan_metrics["contrast"]) == 3000

    assert round(scan_metrics["min_intensity"][0], 2) == -334.00
    assert round(scan_metrics["mean_intensity"][0], 2) == -194.71
    assert round(scan_metrics["max_intensity"][0], 2) == 1727.00
    assert round(scan_metrics["contrast"][0], 2) == 526.00


def test_imaging_quality_metrics_populate(pipeline):
    """
    Assert correct values for entries in the imaging.ProcessingQualityMetrics table.
    Run the `demo_prepare.ipynb` notebook, prior to running this test.
    """
    imaging = pipeline["imaging"]

    key = dict(
        subject="subject1",
        session_datetime=datetime.datetime(2023, 5, 11, 12, 00, 00),
        scan_id=0,
        paramset_idx=0,
        curation_id=0,
        mask=0,
    )

    with verbose_context:
        imaging.ProcessingQualityMetrics.populate(key)

    mask_metrics = (imaging.ProcessingQualityMetrics.Mask() & key).fetch1()
    trace_metrics = (imaging.ProcessingQualityMetrics.Trace() & key).fetch1()

    assert mask_metrics["mask_area"] == None
    assert round(mask_metrics["roundness"], 2) == 0.75
    assert round(trace_metrics["skewness"], 2) == 2.29
    assert round(trace_metrics["variance"], 2) == 865.22
