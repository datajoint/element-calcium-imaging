import numpy as np
from matplotlib import colors
import plotly.graph_objects as go
from .. import scan


def mask_overlayed_image(
    image, mask_xpix, mask_ypix, cell_mask_ids, low_q=0, high_q=0.99
):
    """Overlay transparent cell masks on average image."""

    q_min, q_max = np.quantile(image, [low_q, high_q])
    image = np.clip(image, q_min, q_max)
    image = (image - q_min) / (q_max - q_min)

    SATURATION = 0.7
    image = image[:, :, None] * np.array([0, 0, 1])
    maskid_image = np.full(image.shape[:2], -1)
    for xpix, ypix, roi_id in zip(mask_xpix, mask_ypix, cell_mask_ids):
        image[ypix, xpix, :2] = [np.random.rand(), SATURATION]
        maskid_image[ypix, xpix] = roi_id
    image = (colors.hsv_to_rgb(image) * 255).astype(int)
    return image, maskid_image


def get_tracelayout(key, width=600, height=600):
    """Returns a dictionary of layout settings for the trace figures."""
    text = f"Trace for Cell {key['mask']}" if isinstance(key, dict) else "Trace"

    return dict(
        margin=dict(l=0, r=0, b=0, t=65, pad=0),
        width=width,
        height=height,
        transition={"duration": 0},
        title={
            "text": text,
            "xanchor": "center",
            "yanchor": "top",
            "y": 0.97,
            "x": 0.5,
        },
        xaxis={
            "title": "Time (sec)",
            "visible": True,
            "showticklabels": True,
            "showgrid": True,
        },
        yaxis={
            "title": "Fluorescence (a.u.)",
            "visible": True,
            "showticklabels": True,
            "showgrid": True,
            "anchor": "free",
            "overlaying": "y",
            "side": "left",
            "position": 0,
        },
        yaxis2={
            "title": "Calcium Event (a.u.)",
            "visible": True,
            "showticklabels": True,
            "showgrid": True,
            "anchor": "free",
            "overlaying": "y",
            "side": "right",
            "position": 1,
        },
        shapes=[
            go.layout.Shape(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1.0,
                y1=1.0,
                line={"width": 1, "color": "black"},
            )
        ],
        legend={
            "traceorder": "normal",
            "yanchor": "top",
            "y": 0.99,
            "xanchor": "right",
            "x": 0.99,
        },
        plot_bgcolor="rgba(0,0,0,0.05)",
        modebar_remove=[
            "zoom",
            "resetScale",
            "pan",
            "select",
            "zoomIn",
            "zoomOut",
            "autoScale2d",
        ],
    )


def figure_data(imaging, segmentation_key):
    """Prepare the images for a given segmentation_key.

    Args:
        imaging (dj.Table): imaging table.
        segmentation_key (dict): A primary key from Segmentation table.

    Returns:
        background_with_cells (np.array): Average image with transparently overlayed
            cells.
        cells_maskid_image (np.array): Mask ID image.
    """

    image = (imaging.MotionCorrection.Summary & segmentation_key).fetch1(
        "average_image"
    )

    cell_mask_ids, mask_xpix, mask_ypix = (
        imaging.Segmentation.Mask * imaging.MaskClassification.MaskType
        & segmentation_key
    ).fetch("mask", "mask_xpix", "mask_ypix")

    background_with_cells, cells_maskid_image = mask_overlayed_image(
        image, mask_xpix, mask_ypix, cell_mask_ids, low_q=0, high_q=0.99
    )

    return background_with_cells, cells_maskid_image


def plot_cell_overlayed_image(imaging, segmentation_key):
    """_summary_

    Args:
        imaging (dj.Table): imaging table.
        segmentation_key (dict): A primary key from Segmentation table.

    Returns:
        image_fig (plotly.Fig): Plotly figure object of the average image with
            transparently overlayed cells.
    """

    background_with_cells, cells_maskid_image = figure_data(imaging, segmentation_key)

    image_fig = go.Figure(
        go.Image(
            z=background_with_cells,
            hovertemplate="x: %{x} <br>y: %{y} <br>mask_id: %{customdata}",
            customdata=cells_maskid_image,
        )
    )
    image_fig.update_layout(
        title="Average Image with Cells",
        xaxis={
            "title": "X (px)",
            "visible": True,
            "showticklabels": True,
            "showgrid": False,
        },
        yaxis={
            "title": "Y (px)",
            "visible": True,
            "showticklabels": True,
            "showgrid": False,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return image_fig


def plot_cell_traces(imaging, cell_key):
    """Prepare plotly trace figure.

    Args:
        imaging (dj.Table): imaging table.
        cell_key (dict): A primary key from imaging.Activity.Trace table.

    Returns:
        trace_fig: Plotly figure object of the traces.
    """
    activity_trace = (
        imaging.Activity.Trace & "extraction_method LIKE '%deconvolution'" & cell_key
    ).fetch1("activity_trace")
    fluorescence, fps = (scan.ScanInfo * imaging.Fluorescence.Trace & cell_key).fetch1(
        "fluorescence", "fps"
    )

    trace_fig = go.Figure(
        [
            go.Scatter(
                x=np.arange(len(fluorescence)) / fps,
                y=fluorescence,
                name="Fluorescence",
                yaxis="y1",
            ),
            go.Scatter(
                x=np.arange(len(activity_trace)) / fps,
                y=activity_trace,
                name="Calcium Event",
                yaxis="y2",
            ),
        ]
    )

    trace_fig.update_layout(get_tracelayout(cell_key))

    return trace_fig
