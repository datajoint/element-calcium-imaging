import datajoint as dj

from . import db_prefix

schema = dj.Schema(db_prefix + "reference")


@schema
class Equipment(dj.Manual):
    """Equipment

    Attributes:
        scanner (str): Scanner used in imaging.
    """

    definition = """
    scanner: varchar(32)
    """
