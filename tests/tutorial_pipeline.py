import os
import datajoint as dj
from element_animal import subject
from element_animal.subject import Subject
from element_calcium_imaging import (
    imaging_no_curation as imaging,
    scan,
    imaging_report,
    plotting,
)
from element_lab import lab
from element_lab.lab import Lab, Location, Project, Protocol, Source, User
from element_lab.lab import Device as Equipment
from element_lab.lab import User as Experimenter
from element_session import session_with_datetime as session
from element_session.session_with_datetime import Session
import element_interface
import pathlib


if "custom" not in dj.config:
    dj.config["custom"] = {}

# overwrite dj.config['custom'] values with environment variables if available

dj.config["custom"]["database.prefix"] = os.getenv(
    "DATABASE_PREFIX", dj.config["custom"].get("database.prefix", "")
)

dj.config["custom"]["imaging_root_data_dir"] = os.getenv(
    "IMAGING_ROOT_DATA_DIR", dj.config["custom"].get("imaging_root_data_dir", "")
)

db_prefix = dj.config["custom"].get("database.prefix", "")


# Declare functions for retrieving data
def get_imaging_root_data_dir():
    """Retrieve imaging root data directory."""
    imaging_root_dirs = dj.config.get("custom", {}).get("imaging_root_data_dir", None)
    if not imaging_root_dirs:
        return None
    elif isinstance(imaging_root_dirs, (str, pathlib.Path)):
        return [imaging_root_dirs]
    elif isinstance(imaging_root_dirs, list):
        return imaging_root_dirs
    else:
        raise TypeError("`imaging_root_data_dir` must be a string, pathlib, or list")


def get_calcium_imaging_files(scan_key, acq_software: str):
    """Retrieve the list of absolute paths of the calcium imaging files associated with a given Scan and a given acquisition software (e.g. "ScanImage", "PrairieView", etc.)."""
    # Folder structure: root / subject / session / .tif or .sbx or .nd2
    session_dir = element_interface.utils.find_full_path(
        get_imaging_root_data_dir(),
        (session.SessionDirectory & scan_key).fetch1("session_dir"),
    )

    if acq_software == "ScanImage":
        filepaths = [fp.as_posix() for fp in session_dir.glob("*.tif")]
    elif acq_software == "Scanbox":
        filepaths = [fp.as_posix() for fp in session_dir.glob("*.sbx")]
    elif acq_software == "NIS":
        filepaths = [fp.as_posix() for fp in session_dir.glob("*.nd2")]
    elif acq_software == "PrairieView":
        filepaths = [fp.as_posix() for fp in session_dir.glob("*.tif")]
    else:
        raise NotImplementedError(f"{acq_software} is not implemented")

    if not filepaths:
        raise FileNotFoundError(f"No {acq_software} file found in {session_dir}")
    return filepaths


# Activate schemas
lab.activate(db_prefix + "lab")
subject.activate(db_prefix + "subject", linking_module=__name__)
session.activate(db_prefix + "session", linking_module=__name__)
imaging.activate(db_prefix + "imaging", db_prefix + "scan", linking_module=__name__)
