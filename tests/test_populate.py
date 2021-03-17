import numpy as np

from . import (dj_config, pipeline, subjects_csv, ingest_subjects, sessions_csv, ingest_sessions,
               testdata_paths, suite2p_paramset, caiman2D_paramset, caiman3D_paramset,
               scan_info, processing_tasks, processing, curations)


def test_scan_info_populate_scanimage_2D(testdata_paths, pipeline, scan_info):
    _, _, _, scan, _, _, _ = pipeline
    rel_path = testdata_paths['scanimage_2d']
    scan_key = (scan.ScanInfo & (scan.ScanInfo.ScanFile
                                 & f'file_path LIKE "%{rel_path}%"')).fetch1('KEY')
    nfields, nchannels, ndepths, nframes = (scan.ScanInfo & scan_key).fetch1(
        'nfields', 'nchannels', 'ndepths', 'nframes')

    assert nfields == 1
    assert nchannels == 2
    assert ndepths == 1
    assert nframes == 25000


def test_scan_info_populate_scanimage_3D(testdata_paths, pipeline, scan_info):
    _, _, _, scan, _, _, _ = pipeline
    rel_path = testdata_paths['scanimage_3d']
    scan_key = (scan.ScanInfo & (scan.ScanInfo.ScanFile
                                 & f'file_path LIKE "%{rel_path}%"')).fetch1('KEY')
    nfields, nchannels, ndepths, nframes = (scan.ScanInfo & scan_key).fetch1(
        'nfields', 'nchannels', 'ndepths', 'nframes')

    assert nfields == 3
    assert nchannels == 2
    assert ndepths == 3
    assert nframes == 2000


def test_scan_info_populate_scanbox_3D(testdata_paths, pipeline, scan_info):
    _, _, _, scan, _, _, _ = pipeline
    rel_path = testdata_paths['scanbox_3d']
    scan_key = (scan.ScanInfo & (scan.ScanInfo.ScanFile
                                 & f'file_path LIKE "%{rel_path}%"')).fetch1('KEY')
    nfields, nchannels, ndepths, nframes = (scan.ScanInfo & scan_key).fetch1(
        'nfields', 'nchannels', 'ndepths', 'nframes')

    assert nfields == 4
    assert nchannels == 1
    assert ndepths == 4
    assert nframes == 7530


def test_processing_populate(processing, pipeline):
    _, _, imaging, _, _, _, _ = pipeline
    assert len(imaging.Processing()) == 5


def test_motion_correction_populate_suite2p_2D(processing, pipeline, testdata_paths):
    _, _, imaging, scan, _, _, _ = pipeline

    rel_path = testdata_paths['suite2p_2d']
    processing_key = (imaging.ProcessingTask & f'processing_output_dir LIKE "%{rel_path}"').fetch1('KEY')
    imaging.MotionCorrection.populate(processing_key)

    assert len(imaging.MotionCorrection.Block & processing_key) == 9

    x_shifts = (imaging.MotionCorrection.RigidMotionCorrection & processing_key).fetch1('x_shifts')
    assert len(x_shifts) == (scan.ScanInfo & processing_key).fetch1('nframes')

    ave_img = (imaging.MotionCorrection.Summary & processing_key).fetch1('average_image')
    img_width, img_height = (scan.ScanInfo.Field & processing_key).fetch1('px_width', 'px_height')
    assert ave_img.shape == (img_height, img_width)


def test_motion_correction_populate_suite2p_3D(processing, pipeline, testdata_paths):
    _, _, imaging, scan, _, _, _ = pipeline

    rel_path = testdata_paths['suite2p_3d_a']
    processing_key = (imaging.ProcessingTask & f'processing_output_dir LIKE "%{rel_path}"').fetch1('KEY')
    imaging.MotionCorrection.populate(processing_key)

    assert len(imaging.MotionCorrection.Block & processing_key) == 36

    x_shifts = (imaging.MotionCorrection.RigidMotionCorrection & processing_key).fetch1('x_shifts')
    nfields, nframes = (scan.ScanInfo & processing_key).fetch1('nfields', 'nframes')
    assert x_shifts.shape == (nfields, nframes)

    rel_path = testdata_paths['suite2p_3d_b']
    processing_key = (imaging.ProcessingTask & f'processing_output_dir LIKE "%{rel_path}"').fetch1('KEY')
    imaging.MotionCorrection.populate(processing_key)

    assert len(imaging.MotionCorrection.Block & processing_key) == 54

    x_shifts = (imaging.MotionCorrection.RigidMotionCorrection & processing_key).fetch1('x_shifts')
    nfields, nframes = (scan.ScanInfo & processing_key).fetch1('nfields', 'nframes')
    assert x_shifts.shape == (nfields, nframes)


def test_segmentation_populate_suite2p_2D(curations, pipeline, testdata_paths):
    _, _, imaging, scan, _, _, _ = pipeline

    rel_path = testdata_paths['suite2p_2d']
    curations_key = (imaging.curations & f'curations_output_dir LIKE "%{rel_path}"').fetch1('KEY')

    imaging.Segmentation.populate(curations_key)
    imaging.Fluorescence.populate(curations_key)
    imaging.Activity.populate(curations_key)

    assert len(imaging.Segmentation.Mask & curations_key) == 57

    assert len(imaging.MaskClassification.MaskType & curations_key
               & 'mask_classification_method = "suite2p_default_classifier"'
               & 'mask_type = "soma"') == 27

    assert len(imaging.Fluorescence.Trace & curations_key & 'fluo_channel = 0') == 57
    assert len(imaging.Fluorescence.Trace & curations_key & 'fluo_channel = 0') == 57
    assert len(imaging.Activity.Trace & curations_key
               & 'fluo_channel = 0' & 'extraction_method = "suite2p_deconvolution"') == 57

    nframes = (scan.ScanInfo & curations_key).fetch1('nframes')
    f, fneu = (imaging.Fluorescence.Trace & curations_key
               & 'fluo_channel = 0' & 'mask = 0').fetch1('fluorescence', 'neuropil_fluorescence')
    assert len(f) == len(fneu) == nframes


def test_segmentation_populate_suite2p_3D(curations, pipeline, testdata_paths):
    _, _, imaging, scan, _, _, _ = pipeline

    rel_path = testdata_paths['suite2p_3d_a']
    curations_key = (imaging.curations & f'curations_output_dir LIKE "%{rel_path}"').fetch1('KEY')

    imaging.Segmentation.populate(curations_key)
    imaging.Fluorescence.populate(curations_key)
    imaging.Activity.populate(curations_key)

    assert len(imaging.Segmentation.Mask & curations_key) == 1174

    assert len(imaging.MaskClassification.MaskType & curations_key
               & 'mask_classification_method = "suite2p_default_classifier"'
               & 'mask_type = "soma"') == 432

    assert len(imaging.Fluorescence.Trace & curations_key & 'fluo_channel = 0') == 1174
    assert len(imaging.Fluorescence.Trace & curations_key & 'fluo_channel = 0') == 1174
    assert len(imaging.Activity.Trace & curations_key
               & 'fluo_channel = 0' & 'extraction_method = "suite2p_deconvolution"') == 1174

    nframes = (scan.ScanInfo & curations_key).fetch1('nframes')
    f, fneu = (imaging.Fluorescence.Trace & curations_key
               & 'fluo_channel = 0' & 'mask = 0').fetch1('fluorescence', 'neuropil_fluorescence')
    assert len(f) == len(fneu) == nframes

    rel_path = testdata_paths['suite2p_3d_b']
    curations_key = (imaging.curations & f'curations_output_dir LIKE "%{rel_path}"').fetch1('KEY')

    imaging.Segmentation.populate(curations_key)
    imaging.Fluorescence.populate(curations_key)
    imaging.Activity.populate(curations_key)

    assert len(imaging.Segmentation.Mask & curations_key) == 6636

    assert len(imaging.MaskClassification.MaskType & curations_key
               & 'mask_classification_method = "suite2p_default_classifier"'
               & 'mask_type = "soma"') == 2910

    assert len(imaging.Fluorescence.Trace & curations_key & 'fluo_channel = 0') == 6636
    assert len(imaging.Fluorescence.Trace & curations_key & 'fluo_channel = 0') == 6636
    assert len(imaging.Activity.Trace & curations_key
               & 'fluo_channel = 0' & 'extraction_method = "suite2p_deconvolution"') == 6636

    nframes = (scan.ScanInfo & curations_key).fetch1('nframes')
    f, fneu = (imaging.Fluorescence.Trace & curations_key
               & 'fluo_channel = 0' & 'mask = 0').fetch1('fluorescence', 'neuropil_fluorescence')
    assert len(f) == len(fneu) == nframes
