import datajoint as dj
from elements_animal import subject
from elements_lab import lab
from elements_imaging import scan, imaging

from elements_lab.lab import Source, Lab, Protocol, User

from .paths import (get_imaging_root_data_dir, get_scan_image_files,
                    get_suite2p_dir, get_caiman_dir)


if 'custom' not in dj.config:
    dj.config['custom'] = {}

db_prefix = dj.config['custom'].get('database.prefix', '')


# ------------- Activate "lab" and "subject" schema -------------

lab.activate(db_prefix + 'lab')

subject.activate(db_prefix + 'subject', required_module=__name__)


# ------------- Declare tables Session and Scanner for use in elements_imaging -------------

schema = dj.schema(db_prefix + 'experiment')


@schema
class Session(dj.Manual):
    definition = """
    -> subject.Subject
    session_datetime: datetime
    """


@schema
class Scanner(dj.Manual):
    definition = """
    scanner: varchar(32)    
    """


# ------------- Activate "imaging" schema -------------
imaging.activate(db_prefix + 'imaging', db_prefix + 'scan', required_module=__name__)
