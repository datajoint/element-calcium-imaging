import datajoint as dj
from collections import abc
from .pipeline import session
from element_interface.utils import find_full_path


def get_imaging_root_data_dir():
    imaging_root_dirs = dj.config.get("custom", {}).get("imaging_root_data_dir", None)
    if not imaging_root_dirs:
        return None
    elif not isinstance(imaging_root_dirs, abc.Sequence):
        return list(imaging_root_dirs)
    else:
        return imaging_root_dirs


def _find_files_by_type(scan_key, filetype: str):
    """Uses roots + relative SessionDirectory, returns list of files with filetype"""
    sess_dir = find_full_path(
        get_imaging_root_data_dir(),
        (session.SessionDirectory & scan_key).fetch1("session_dir"),
    )
    return sess_dir, [fp.as_posix() for fp in sess_dir.glob(filetype)]


def get_scan_image_files(scan_key):
    # Folder structure: root / subject / session / .tif (raw)
    sess_dir, tiff_filepaths = _find_files_by_type(scan_key, "*.tif")
    if tiff_filepaths:
        return tiff_filepaths
    else:
        raise FileNotFoundError(f"No tiff file found in {sess_dir}")


def get_scan_box_files(scan_key):
    # Folder structure: root / subject / session / .sbx
    sess_dir, sbx_filepaths = _find_files_by_type(scan_key, "*.sbx")
    if sbx_filepaths:
        return sbx_filepaths
    else:
        raise FileNotFoundError(f"No .sbx file found in {sess_dir}")


def get_nd2_files(scan_key):
    # Folder structure: root / subject / session / .nd2
    sess_dir, nd2_filepaths = _find_files_by_type(scan_key, "*.nd2")
    if nd2_filepaths:
        return nd2_filepaths
    else:
        raise FileNotFoundError(f"No .nd2 file found in {sess_dir}")
