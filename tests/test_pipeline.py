import datetime


def test_generate_pipeline(pipeline):
    subject = pipeline["subject"]
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]
    session = pipeline["session"]
    Equipment = pipeline["Equipment"]

    # Test connection from Subject to Session
    assert subject.Subject.full_table_name in session.Session.parents()

    # Test connection from Session and Equipment to Scan
    assert session.Session.full_table_name in scan.Scan.parents()
    assert Equipment.full_table_name in scan.Scan.parents()

    assert "mask_npix" in imaging.Segmentation.Mask.heading.secondary_attributes
    assert "activity_trace" in imaging.Activity.Trace.heading.secondary_attributes


def test_scan_info(pipeline, scan_info):
    scan = pipeline["scan"]
    expected_scaninfo = {
        "subject": "subject1",
        "session_datetime": datetime.datetime(2021, 4, 30, 12, 22, 15),
        "scan_id": 0,
        "nfields": 1,
        "nchannels": 1,
        "ndepths": 1,
        "nframes": 3000,
        "nrois": 0,
        "x": 13441.9,
        "y": 15745.0,
        "z": -205821.0,
        "fps": 29.2398,
        "bidirectional": 1,
        "usecs_per_line": 63.0981,
        "fill_fraction": 0.712867,
        "scan_datetime": None,
        "scan_duration": 102.6,
        "bidirectional_z": None,
    }
    scan_info = scan.ScanInfo.fetch1()

    assert scan_info == expected_scaninfo


def test_processing(pipeline, processing):
    imaging = pipeline["imaging"]

    # motion correction
    average_image, correlation_image = imaging.MotionCorrection.Summary.fetch1(
        "average_image", "correlation_image"
    )
    assert average_image.shape == (512, 512)
    assert correlation_image.shape == (504, 506)

    y_shifts, x_shifts = imaging.MotionCorrection.RigidMotionCorrection.fetch1(
        "y_shifts", "x_shifts"
    )
    assert len(y_shifts) == len(x_shifts) == 3000
    assert y_shifts.sum() == 859
    assert x_shifts.sum() == -377

    # segmentation
    masks_npix = imaging.Segmentation.Mask.fetch("mask_npix")
    assert len(masks_npix) == 1276
    assert masks_npix.sum() == 73701
    assert round(masks_npix.mean()) == 58

    assert len(imaging.Segmentation.Mask & imaging.MaskClassification.MaskType) == 481

    # fluorescence
    assert len(imaging.Fluorescence.Trace & "fluo_channel = 0") == 1276
    ftrace = (imaging.Fluorescence.Trace & "fluo_channel = 0" & "mask = 10").fetch1(
        "fluorescence"
    )
    assert len(ftrace) == 3000
    assert ftrace.argmax() == 1031

    # activity
    assert len(imaging.Activity.Trace & "fluo_channel = 0") == 1276
    atrace = (imaging.Activity.Trace & "fluo_channel = 0" & "mask = 20").fetch1(
        "activity_trace"
    )
    assert len(atrace) == 3000
    assert atrace.argmax() == 1597


def test_report(pipeline, report):
    imaging_report = pipeline["imaging_report"]

    assert len(imaging_report.ScanLevelReport()) == 1
    assert len(imaging_report.TraceReport()) == 1276
