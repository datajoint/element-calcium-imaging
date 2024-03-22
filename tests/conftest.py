import os
from pathlib import Path
import datajoint as dj
import pytest


logger = dj.logger
_tear_down = True

# ---------------------- FIXTURES ----------------------


@pytest.fixture(autouse=True, scope="session")
def dj_config():
    """If dj_local_config exists, load"""
    if Path("./dj_local_conf.json").exists():
        dj.config.load("./dj_local_conf.json")
    dj.config.update(
        {
            "safemode": False,
            "database.host": os.environ.get("DJ_HOST") or dj.config["database.host"],
            "database.password": os.environ.get("DJ_PASS")
            or dj.config["database.password"],
            "database.user": os.environ.get("DJ_USER") or dj.config["database.user"],
        }
    )
    os.environ["DATABASE_PREFIX"] = "test_"
    return


@pytest.fixture(autouse=True, scope="session")
def pipeline():
    from . import tutorial_pipeline as pipeline

    yield {
        "lab": pipeline.lab,
        "subject": pipeline.subject,
        "session": pipeline.session,
        "scan": pipeline.scan,
        "imaging": pipeline.imaging,
        "imaging_report": pipeline.imaging_report,
        "Equipment": pipeline.Equipment,
    }

    if _tear_down:
        pipeline.imaging_report.schema.drop()
        pipeline.imaging.schema.drop()
        pipeline.scan.schema.drop()
        pipeline.session.schema.drop()
        pipeline.subject.schema.drop()
        pipeline.lab.schema.drop()


@pytest.fixture(scope="session")
def insert_upstreams(pipeline):
    subject = pipeline["subject"]
    session = pipeline["session"]
    scan = pipeline["scan"]
    Equipment = pipeline["Equipment"]

    subject.Subject.insert1(
        dict(
            subject="subject1",
            subject_nickname="subject1_nickname",
            sex="F",
            subject_birth_date="2020-01-01",
            subject_description="ScanImage acquisition. Suite2p processing.",
        ),
        skip_duplicates=True,
    )

    session_key = dict(subject="subject1", session_datetime="2021-04-30 12:22:15")
    session_dir = "subject1/session1"
    session.Session.insert1(session_key, skip_duplicates=True)
    session.SessionDirectory.insert1(
        dict(**session_key, session_dir=session_dir), skip_duplicates=True
    )

    Equipment.insert1(
        dict(
            device="Scanner1",
            modality="Calcium imaging",
            description="Example microscope",
        ),
        skip_duplicates=True,
    )
    scan.Scan.insert1(
        dict(
            **session_key,
            scan_id=0,
            device="Scanner1",
            acq_software="ScanImage",
            scan_notes="",
        ),
        skip_duplicates=True,
    )

    yield

    if _tear_down:
        subject.Subject.delete()
        Equipment.delete()


@pytest.fixture(scope="session")
def scan_info(pipeline, insert_upstreams):
    scan = pipeline["scan"]
    scan.ScanInfo.populate()

    yield

    if _tear_down:
        scan.ScanInfo.delete()


@pytest.fixture(scope="session")
def insert_processing_task(pipeline, scan_info):
    import suite2p

    imaging = pipeline["imaging"]

    params_suite2p = suite2p.default_ops()
    params_suite2p["nonrigid"] = False

    imaging.ProcessingParamSet.insert_new_params(
        processing_method="suite2p",
        paramset_idx=0,
        params=params_suite2p,
        paramset_desc="Calcium imaging analysis with Suite2p using default parameters",
    )

    session_key = dict(subject="subject1", session_datetime="2021-04-30 12:22:15")
    processing_output_dir = "subject1/session1/suite2p"

    imaging.ProcessingTask.insert1(
        dict(
            **session_key,
            scan_id=0,
            paramset_idx=0,
            task_mode="load",
            processing_output_dir=processing_output_dir,
        ),
        skip_duplicates=True,
    )

    yield

    if _tear_down:
        imaging.ProcessingParamSet.delete()


@pytest.fixture(scope="session")
def processing(pipeline, insert_processing_task):
    imaging = pipeline["imaging"]

    imaging.Processing.populate()
    imaging.MotionCorrection.populate()
    imaging.Segmentation.populate()
    imaging.Fluorescence.populate()
    imaging.Activity.populate()

    yield

    if _tear_down:
        imaging.Processing.delete()


@pytest.fixture(scope="session")
def report(pipeline, processing):
    imaging_report = pipeline["imaging_report"]

    imaging_report.ScanLevelReport.populate(display_progress=True)
    imaging_report.TraceReport.populate(display_progress=True)

    yield

    if _tear_down:
        imaging_report.ScanLevelReport.delete()
        imaging_report.TraceReport.delete()
