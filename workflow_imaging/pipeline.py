import datajoint as dj
from elements_animal import subject
from elements_lab import lab
from elements_imaging import scan, imaging

from elements_lab.lab import Source, Lab, Protocol, User, Location

from .paths import (get_imaging_data_dir, get_scan_image_files,
                    get_suite2p_dir, get_caiman_dir)


if 'custom' not in dj.config:
    dj.config['custom'] = {}

db_prefix = dj.config['custom'].get('database.prefix', '')


# ------------- Activate "lab" and "subject" schema -------------

lab.activate(db_prefix + 'lab')

subject.activate(db_prefix + 'subject', linking_module=__name__)


# ------------- Declare tables Session and Equipment for use in elements_imaging -------------

schema = dj.schema(db_prefix + 'experiment')


@schema
class Session(dj.Manual):
    definition = """
    -> subject.Subject
    session_datetime: datetime
    """


@schema
class Equipment(dj.Manual):
    definition = """
    scanner: varchar(32) 
    """


# ------------- Activate "imaging" and "scan" schemas -------------
scan.activate(db_prefix + 'scan', linking_module=__name__)
imaging.activate(db_prefix + 'imaging',  linking_module=__name__)
