import datajoint as dj
from element_animal import subject
from element_lab import lab
from element_session import session
from element_calcium_imaging import scan, imaging

from element_lab.lab import Source, Lab, Protocol, User, Location, Project
from element_animal.subject import Subject
from element_session.session import Session

from .paths import (get_imaging_root_data_dir,
                    get_scan_image_files, get_scan_box_files)


if 'custom' not in dj.config:
    dj.config['custom'] = {}

db_prefix = dj.config['custom'].get('database.prefix', '')


# ------------- Activate "lab", "subject", "session" schema -------------

lab.activate(db_prefix + 'lab')

subject.activate(db_prefix + 'subject', linking_module=__name__)

session.activate(db_prefix + 'session', linking_module=__name__)

# ------------- Declare table Equipment for use in element_calcium_imaging -------------


@lab.schema
class Equipment(dj.Manual):
    definition = """
    scanner: varchar(32) 
    """


# ------------- Activate "imaging" schema -------------
imaging.activate(db_prefix + 'imaging',  db_prefix + 'scan',  linking_module=__name__)
