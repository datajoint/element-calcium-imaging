import pathlib
import sys

from . import (dj_config, pipeline, test_data,
               subjects_csv, ingest_subjects,
               sessions_csv, ingest_sessions,
               testdata_paths, suite2p_paramset,
               caiman2D_paramset, caiman3D_paramset,
               scan_info,
               processing_tasks,
               processing, curations)


def test_ingest_subjects(pipeline, ingest_subjects):
    subject = pipeline['subject']
    assert len(subject.Subject()) == 4


def test_ingest_sessions(pipeline, sessions_csv, ingest_sessions):
    scan = pipeline['scan']
    session = pipeline['session']
    get_imaging_root_data_dir = pipeline['get_imaging_root_data_dir']

    assert len(session.Session()) == 5
    assert len(scan.Scan()) == 5

    sessions, _ = sessions_csv
    sess = sessions.iloc[4]
    sess_dir = pathlib.Path(sess.session_dir).relative_to(get_imaging_root_data_dir())
    assert (session.SessionDirectory
            & {'subject': sess.name}).fetch1('session_dir') == sess_dir.as_posix()


def test_find_valid_full_path(pipeline, sessions_csv):
    from element_calcium_imaging import find_full_path

    get_imaging_root_data_dir = pipeline['get_imaging_root_data_dir']

    # add more options for root directories
    if sys.platform == 'win32':
        ephys_root_data_dir = [get_imaging_root_data_dir(), 'J:/', 'M:/']
    else:
        ephys_root_data_dir = [get_imaging_root_data_dir(), 'mnt/j', 'mnt/m']

    # test: providing relative-path: correctly search for the full-path
    sessions, _ = sessions_csv
    sess = sessions.iloc[0]
    session_full_path = pathlib.Path(sess.session_dir)

    rel_path = pathlib.Path(session_full_path).relative_to(
        pathlib.Path(get_imaging_root_data_dir()))
    full_path = find_full_path(ephys_root_data_dir, rel_path)

    assert full_path == session_full_path


def test_find_root_directory(pipeline, sessions_csv):
    from element_calcium_imaging import find_root_directory

    get_imaging_root_data_dir = pipeline['get_imaging_root_data_dir']

    # add more options for root directories
    if sys.platform == 'win32':
        ephys_root_data_dir = [get_imaging_root_data_dir(), 'J:/', 'M:/']
    else:
        ephys_root_data_dir = [get_imaging_root_data_dir(), 'mnt/j', 'mnt/m']

    # test: providing full-path: correctly search for the root_dir
    sessions, _ = sessions_csv
    sess = sessions.iloc[0]
    session_full_path = pathlib.Path(sess.session_dir)

    root_dir = find_root_directory(ephys_root_data_dir, session_full_path)

    assert root_dir == get_imaging_root_data_dir()


def test_paramset_insert(suite2p_paramset, caiman2D_paramset, caiman3D_paramset, pipeline):
    imaging = pipeline['imaging']
    from element_calcium_imaging.imaging import dict_to_uuid

    method, desc, paramset_hash = (imaging.ProcessingParamSet & {'paramset_idx': 0}).fetch1(
        'processing_method', 'paramset_desc', 'param_set_hash')
    assert method == 'suite2p'
    assert desc == 'Calcium imaging analysis with Suite2p using default Suite2p parameters'
    assert dict_to_uuid(suite2p_paramset) == paramset_hash

    method, desc, paramset_hash = (imaging.ProcessingParamSet & {'paramset_idx': 1}).fetch1(
        'processing_method', 'paramset_desc', 'param_set_hash')
    assert method == 'caiman'
    assert desc == 'Calcium imaging analysis' \
                   ' with CaImAn using default CaImAn parameters for 2d planar images'
    assert dict_to_uuid(caiman2D_paramset) == paramset_hash

    method, desc, paramset_hash = (imaging.ProcessingParamSet & {'paramset_idx': 2}).fetch1(
        'processing_method', 'paramset_desc', 'param_set_hash')
    assert method == 'caiman'
    assert desc == 'Calcium imaging analysis' \
                   ' with CaImAn using default CaImAn parameters for 3d volumetric images'
    assert dict_to_uuid(caiman3D_paramset) == paramset_hash
