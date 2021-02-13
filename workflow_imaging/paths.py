import datajoint as dj
import pathlib


def get_imaging_root_data_dir():
    data_dir = dj.config.get('custom', {}).get('imaging_root_data_dir', None)
    return pathlib.Path(data_dir) if data_dir else None


def get_scan_image_files(scan_key):
    # Folder structure: root / subject / session / .tif (raw)
    data_dir = get_imaging_root_data_dir()

    from .pipeline import Session
    sess_dir = data_dir / (Session.Directory & scan_key).fetch1('session_dir')

    if not sess_dir.exists():
        raise FileNotFoundError(f'Session directory not found ({sess_dir})')

    tiff_filepaths = [fp.as_posix() for fp in sess_dir.glob('*.tif')]
    if tiff_filepaths:
        return tiff_filepaths
    else:
        raise FileNotFoundError(f'No ScanImage file (.tif) found in {sess_dir}')


def get_scan_box_files(scan_key):
    # Folder structure: root / subject / session / .sbx
    data_dir = get_imaging_root_data_dir()

    from .pipeline import Session
    sess_dir = data_dir / (Session.Directory & scan_key).fetch1('session_dir')

    if not sess_dir.exists():
        raise FileNotFoundError(f'Session directory not found ({sess_dir})')

    sbx_filepaths = [fp.as_posix() for fp in sess_dir.glob('*.sbx')]
    if sbx_filepaths:
        return sbx_filepaths
    else:
        raise FileNotFoundError(f'No ScanBox file (.sbx) found in {sess_dir}')

def get_miniscope_daq_file(scan_key):
    # Folder structure: root / subject / session / .json
    data_dir = get_imaging_root_data_dir()

    from .pipeline import Session
    sess_dir = data_dir / (Session.Directory & scan_key).fetch1('session_dir')

    if not sess_dir.exists():
        raise FileNotFoundError(f'Session directory not found ({sess_dir})')

    ma_filepaths = [fp.as_posix() for fp in sess_dir.glob('*.json')]
    if ma_filepaths:
        return ma_filepaths[0]
    else:
        raise FileNotFoundError(f'No Miniscope-DAQ file (.json) found in {sess_dir}')

def get_suite2p_dir(processing_task_key):
    # Folder structure: root / subject / session / suite2p / plane / suite2p_ops.npy
    data_dir = get_imaging_root_data_dir()

    from .pipeline import Session
    sess_dir = data_dir / (Session.Directory & processing_task_key).fetch1('session_dir')

    if not sess_dir.exists():
        raise FileNotFoundError(f'Session directory not found ({sess_dir})')

    suite2p_dirs = set([fp.parent.parent for fp in sess_dir.rglob('*ops.npy')])
    if len(suite2p_dirs) != 1:
        raise FileNotFoundError(f'Error searching for Suite2p output directory in {sess_dir} - Found {suite2p_dirs}')

    return suite2p_dirs.pop()


def get_caiman_dir(processing_task_key):
    # Folder structure: root / subject / session / caiman / *.hdf5
    data_dir = get_imaging_root_data_dir()

    from .pipeline import Session
    sess_dir = data_dir / (Session.Directory & processing_task_key).fetch1('session_dir')

    if not sess_dir.exists():
        raise FileNotFoundError(f'Session directory not found ({sess_dir})')

    caiman_dir = sess_dir / 'caiman'

    if not caiman_dir.exists():
        raise FileNotFoundError(f'CaImAn directory not found at {caiman_dir}')

    return caiman_dir
