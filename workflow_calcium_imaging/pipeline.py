import datajoint as dj
from element_lab import lab
from element_animal import subject
from element_session import session_with_datetime as session
from element_event import trial, event
from element_calcium_imaging import scan, imaging
from element_lab.lab import Source, Lab, Protocol, User, Location, Project
from element_animal.subject import Subject
from . import analysis

if "custom" not in dj.config:
    dj.config["custom"] = {}

db_prefix = dj.config["custom"].get("database.prefix", "")

__all__ = [
    "subject",
    "lab",
    "session",
    "Equipment",
    "trial",
    "event",
    "scan",
    "imaging",
    "Subject",
    "Source",
    "Lab",
    "Protocol",
    "User",
    "Project",
    "Session",
    "Location",
]


# ------------- Activate "lab", "subject", "session" schema -------------

lab.activate(db_prefix + "lab")

subject.activate(db_prefix + "subject", linking_module=__name__)

Session = session.Session
Experimenter = lab.User
session.activate(db_prefix + "session", linking_module=__name__)


# Activate "event" and "trial" schema ---------------------------------

trial.activate(db_prefix + "trial", db_prefix + "event", linking_module=__name__)


# ------------- Declare table Equipment for use in element_calcium_imaging -------------


@lab.schema
class Equipment(dj.Manual):
    """Equipment

    Attributes:
        scanner (str): Scanner used in imaging.
    """

    definition = """
    scanner: varchar(32)
    """


# ------------- Activate "imaging" schema -------------

imaging.activate(db_prefix + "imaging", db_prefix + "scan", linking_module=__name__)

# ------------- Activate "analysis" schema ------------

analysis.activate(db_prefix + "analysis", linking_module=__name__)
