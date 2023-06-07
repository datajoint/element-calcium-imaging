import datajoint as dj
from element_animal import subject
from element_animal.subject import Subject
from element_calcium_imaging import imaging, scan, imaging_report, db_prefix, plotting
from element_lab import lab
from element_lab.lab import Lab, Location, Project, Protocol, Source, User
from element_lab.lab import Device as Equipment
from element_lab.lab import User as Experimenter
from element_session import session_with_datetime as session
from element_session.session_with_datetime import Session
import element_interface



# Declare functions for retrieving data
def get_imaging_root_data_dir():
    """Retrieve imaging root data directory."""
    imaging_root_dirs = dj.config.get("custom", {}).get("imaging_root_data_dir", None)
    if not imaging_root_dirs:
        return None
    return list(imaging_root_dirs)


def get_image_files(scan_key, file_type: str):
    """Retrieve the list of absolute paths associated with a given Scan."""
    # Folder structure: root / subject / session / .tif or .sbx or .nd2
    session_dir = element_interface.utils.find_full_path(
        get_imaging_root_data_dir(),
        (session.SessionDirectory & scan_key).fetch1("session_dir"),
    )

    filepaths = [fp.as_posix() for fp in session_dir.glob(file_type)]

    if not filepaths:
        raise FileNotFoundError(f"No {file_type} file found in {session_dir}")
    return filepaths


# Activate schemas
lab.activate(db_prefix + "lab")
subject.activate(db_prefix + "subject", linking_module=__name__)
session.activate(db_prefix + "session", linking_module=__name__)
imaging.activate(db_prefix + "imaging", db_prefix + "scan", linking_module=__name__)
