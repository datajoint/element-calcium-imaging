import datajoint as dj
from .plotting import cell_plot

schema = dj.Schema()

imaging = None


def activate(
    schema_name, imaging_schema_name, *, create_schema=True, create_tables=True
):
    """Activate this schema.

    Args:
        schema_name (str): Schema name on the database server to activate the
            `imaging_report` schema
        imaging_schema_name (str): Schema name of the activated imaging element for
            which this imaging_report schema will be downstream from
        create_schema: When True (default), create schema in the database if it does not
            yet exist.
        create_tables: When True (default), create tables in the database if they do not
            yet exist.
    """
    global imaging
    imaging = dj.create_virtual_module("imaging", imaging_schema_name)

    schema.activate(
        schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        add_objects=imaging.__dict__,
    )


@schema
class ScanLevelReport(dj.Computed):
    """Scan level report with figures.

    Attributes:
        imaging.Segmentation (foreign key): Primary key from imaging.Segmentation.
        cell_overlayed_image (longblob): Plotly figure object showing the segmented
            cells on the average image.
    """

    definition = """
    -> imaging.Segmentation
    ---
    cell_overlayed_image: longblob
    """

    def make(self, key):
        """Compute and ingest the plotly figure objects."""

        image_fig = cell_plot.plot_cell_overlayed_image(imaging, key)
        self.insert1({**key, "cell_overlayed_image": image_fig.to_json()})


@schema
class TraceReport(dj.Computed):
    """Figures of traces.

    Attributes:
        imaging.Segmentation.Mask (foreign key): Primary key from
            imaging.Segmentation.Mask.
        cell_traces (longblob): Plotly figure object showing the cell traces.
    """

    definition = """
    -> imaging.Segmentation.Mask
    ---
    cell_traces: longblob
    """

    @property
    def key_source(self):
        """Limit the TraceReport to Masks that have Activity table populated.
        database."""

        return imaging.Segmentation.Mask & imaging.Activity

    def make(self, key):
        """Compute and ingest the plotly figure objects."""

        trace_fig = cell_plot.plot_cell_traces(imaging, key)
        self.insert1({**key, "cell_traces": trace_fig.to_json()})
