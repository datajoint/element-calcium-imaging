import sys
import pathlib
from . import (
    dj_config,
    pipeline,
    test_data,
    subjects_csv,
    ingest_subjects,
    sessions_csv,
    ingest_sessions,
    testdata_paths,
    suite2p_paramset,
    caiman2D_paramset,
    caiman3D_paramset,
    scan_info,
    processing_tasks,
    processing,
    curations,
)
from element_interface.utils import find_full_path, find_root_directory


def test_ingest_subjects(pipeline, ingest_subjects):
    subject = pipeline["subject"]
    assert len(subject.Subject()) == 4


def test_ingest_sessions(pipeline, sessions_csv, ingest_sessions):
    scan = pipeline["scan"]
    session = pipeline["session"]
    get_imaging_root_data_dir = pipeline["get_imaging_root_data_dir"]

    assert len(session.Session()) == 5
    assert len(scan.Scan()) == 5

    sessions, _ = sessions_csv
    sess_dir_full = sessions.iloc[4].session_dir
    sess_dir_root = find_root_directory(get_imaging_root_data_dir(), sess_dir_full)
    assert (session.SessionDirectory & {"subject": sessions.iloc[4].name}).fetch1(
        "session_dir"
    ) == str(sess_dir_full.relative_to(sess_dir_root))


def test_find_valid_full_path(pipeline, sessions_csv):
    get_imaging_root_data_dir = pipeline["get_imaging_root_data_dir"]

    # add more options for root directories
    if sys.platform == "win32":
        imaging_root_data_dirs = get_imaging_root_data_dir() + ["J:/", "M:/"]
    else:
        imaging_root_data_dirs = get_imaging_root_data_dir() + ["mnt/j", "mnt/m"]

    # test: providing relative-path: correctly search for the full-path
    sessions, _ = sessions_csv
    sess_dir_full = sessions.iloc[0].session_dir
    sess_dir_root = find_root_directory(get_imaging_root_data_dir(), sess_dir_full)
    sess_dir_rel = sess_dir_full.relative_to(sess_dir_root)
    full_path = find_full_path(imaging_root_data_dirs, sess_dir_rel)

    assert full_path == sess_dir_full


def test_find_root_directory(pipeline, sessions_csv):
    get_imaging_root_data_dir = pipeline["get_imaging_root_data_dir"]

    # add more options for root directories
    if sys.platform == "win32":
        imaging_root_data_dirs = get_imaging_root_data_dir() + ["J:/", "M:/"]
    else:
        imaging_root_data_dirs = get_imaging_root_data_dir() + ["mnt/j", "mnt/m"]

    # test: providing full-path: correctly search for the root_dir
    sessions, _ = sessions_csv
    sess_dir_full = sessions.iloc[0].session_dir
    sess_dir_root = find_root_directory(get_imaging_root_data_dir(), sess_dir_full)

    test_root_dir = find_root_directory(imaging_root_data_dirs, sess_dir_full)

    assert test_root_dir == sess_dir_root


def test_paramset_insert(
    suite2p_paramset, caiman2D_paramset, caiman3D_paramset, pipeline
):
    imaging = pipeline["imaging"]
    from element_interface.utils import dict_to_uuid

    method, desc, paramset_hash = (
        imaging.ProcessingParamSet & {"paramset_idx": 0}
    ).fetch1("processing_method", "paramset_desc", "param_set_hash")
    assert method == "suite2p"
    assert (
        desc == "Calcium imaging analysis with Suite2p using default Suite2p parameters"
    )
    assert dict_to_uuid(suite2p_paramset) == paramset_hash

    method, desc, paramset_hash = (
        imaging.ProcessingParamSet & {"paramset_idx": 1}
    ).fetch1("processing_method", "paramset_desc", "param_set_hash")
    assert method == "caiman"
    assert (
        desc == "Calcium imaging analysis"
        " with CaImAn using default CaImAn parameters for 2d planar images"
    )
    assert dict_to_uuid(caiman2D_paramset) == paramset_hash

    method, desc, paramset_hash = (
        imaging.ProcessingParamSet & {"paramset_idx": 2}
    ).fetch1("processing_method", "paramset_desc", "param_set_hash")
    assert method == "caiman"
    assert (
        desc == "Calcium imaging analysis"
        " with CaImAn using default CaImAn parameters for 3d volumetric images"
    )
    assert dict_to_uuid(caiman3D_paramset) == paramset_hash
