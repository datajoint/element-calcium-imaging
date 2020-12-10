import datajoint as dj

from djutils.templates import SchemaTemplate, required

schema = SchemaTemplate()


@schema
class PhysicalFile(dj.Manual):
    definition = """
    file_path: varchar(255)  # filepath relative to root data directory
    """

    @staticmethod
    @required
    def _get_root_data_dir() -> str:
        """
        Get the full path for the root data directory (e.g. the mounted drive)
        :return: a string with full path to the root data directory
        """
        return None
