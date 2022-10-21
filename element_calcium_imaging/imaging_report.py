import datajoint as dj

from . import scan
from .plotting import cell_plot


schema = imaging.schema


imaging = None


def _activate(
    schema_name, *, create_schema=True, create_tables=True
):
    """
    activate(schema_name, *, create_schema=True, create_tables=True)
        :param schema_name: schema name on the database server to activate the `probe` element
        :param create_schema: when True (default), create schema in the database if it does not yet exist.
        :param create_tables: when True (default), create tables in the database if they do not yet exist.
    (The "activation" of this imaging_report module should be evoked by one of the imaging modules only)
    """
    global imaging
    imaging = dj.create_virtual_module("vm", schema_name)

    schema.activate(
        schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        add_objects=imaging.__dict__,
    )


@schema
class ScanLevelReport(dj.Computed):
    definition = """
    -> imaging.Segmentation
    ---
    average_image: longblob
    """

    def make(self, key):
        image_fig = cell_plot.plot_cell_overlayed_image(imaging, key)
        self.insert1({**key, "average_image": image_fig.to_json()})


@schema
class ActivityReport(dj.Computed):
    definition = """
    -> imaging.Segmentation.Mask
    ---
    activity_trace: longblob
    """

    def make(self, key):
        trace_fig = cell_plot.plot_cell_traces(imaging, key)
        self.insert1({**key, "activity_trace": trace_fig.to_json()})
