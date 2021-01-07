import datajoint as dj
import pathlib


def get_imaging_root_data_dir():
    data_dir = dj.config.get('custom', {}).get('imaging_root_data_dir', None)
    return pathlib.Path(data_dir) if data_dir else None


def get_scan_image_files(scan_key):
    # Folder structure: root / subject / session / .tif (raw)
    data_dir = get_imaging_root_data_dir()
    subj_dir = data_dir / scan_key['subject']
    sess_datetime_string = scan_key['session_datetime'].strftime('%Y%m%d_%H%M%S')
    sess_dir = subj_dir / sess_datetime_string

    if not sess_dir.exists():
        raise FileNotFoundError(f'Session directory not found ({sess_dir})')

    tiff_filepaths = [fp.as_posix() for fp in sess_dir.glob('*.tif')]
    if tiff_filepaths:
        return tiff_filepaths
    else:
        raise FileNotFoundError(f'No tiff file found in {sess_dir}')


def get_suite2p_dir(processing_task_key):
    # Folder structure: root / subject / session / suite2p / plane / suite2p_ops.npy

    tiff_filepaths = get_scan_image_files(processing_task_key)
    sess_folder = pathlib.Path(tiff_filepaths[0]).parent

    suite2p_dirs = set([fp.parent.parent for fp in sess_folder.rglob('*ops.npy')])
    if len(suite2p_dirs) != 1:
        raise FileNotFoundError(f'Error searching for Suite2p output directory in {sess_folder} - Found {suite2p_dirs}')

    return suite2p_dirs.pop()


def get_caiman_dir(processing_task_key):
    # Folder structure: root / subject / session / caiman / *.hdf5

    tiff_filepaths = get_scan_image_files(processing_task_key)
    sess_dir = pathlib.Path(tiff_filepaths[0]).parent
    caiman_dir = sess_dir / 'caiman'

    if not caiman_dir.exists():
        raise FileNotFoundError('CaImAn directory not found at {}'.format(caiman_dir))

    return caiman_dir
