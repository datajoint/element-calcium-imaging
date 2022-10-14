import cv2
import numpy as np
import datajoint as dj
from functools import partial
from plotly.io import from_json
import plotly.graph_objects as go
from ipywidgets import widgets as wg
from . import imaging, scan

schema = imaging.schema


def single_to_3channel_image(image, low_q, high_q):
    low_p, high_p = np.percentile(image, [low_q, high_q])
    image = np.clip(image, low_p, high_p)
    image = np.uint8(255 * (image - low_p) / (high_p - low_p))
    return np.dstack([image] * 3)


def paint_rois(image, mask_xpix, mask_ypix):
    # Generate random hsv colors
    SATURATION = 40
    VALUE = 255
    hues = np.random.sample(size=len(mask_xpix)) * 10000
    hsv_colors = np.stack(
        [hues, np.full(len(mask_xpix), SATURATION), np.full(len(mask_xpix), VALUE)]
    ).T

    # Assign colors to each region
    masks = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    for xpix, ypix, hsv_color in zip(mask_xpix, mask_ypix, hsv_colors):
        masks[ypix, xpix] = hsv_color

    masks = np.uint8(cv2.cvtColor(masks.astype(np.float32), cv2.COLOR_HSV2RGB))
    return masks


def alpha_combine_2images(image, masks):
    alpha = 0.5
    return np.uint8(image * alpha + masks * (1 - alpha))


def make_maskid_image(img, roi_ids, mask_xpix, mask_ypix):
    shape = img.shape[:2]
    maskid_image = np.full(shape, -1)
    for xpix, ypix, roi_id in zip(mask_xpix, mask_ypix, roi_ids):
        maskid_image[ypix, xpix] = roi_id
    return maskid_image


def get_tracelayout(key, width=600, height=600):
    text = f"Trace for Cell {key['mask']}" if isinstance(key, dict) else "Trace"

    return dict(
        margin=dict(l=0, r=0, b=0, t=65, pad=0),
        width=width,
        height=height,  # 700,
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
            "titlefont": dict(color="#d62728"),
            "tickfont": dict(color="#d62728"),
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


@schema
class ScanLevelReport(dj.Computed):
    definition = """
    -> imaging.Segmentation
    ---
    average_image: longblob
    """

    def make(self, key):
        image = (imaging.MotionCorrection.Summary & key).fetch1("average_image")

        cell_mask_ids, mask_xpix, mask_ypix = (
            imaging.Segmentation.Mask * imaging.MaskClassification.MaskType & key
        ).fetch("mask", "mask_xpix", "mask_ypix")

        background_image = single_to_3channel_image(image, 1, 99)

        background_image_with_cells_painted = paint_rois(
            background_image, mask_xpix, mask_ypix
        )
        cells_maskid_image = make_maskid_image(
            background_image[:, :, 0], cell_mask_ids, mask_xpix, mask_ypix
        )
        background_with_cells = alpha_combine_2images(
            background_image, background_image_with_cells_painted
        )

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

        self.insert1({**key, "average_image": image_fig.to_json()})


@schema
class ActivityReport(dj.Computed):
    definition = """
    -> imaging.Segmentation.Mask
    ---
    activity_trace: longblob
    """

    def make(self, key):
        activity_trace = (
            imaging.Activity.Trace & "extraction_method LIKE '%deconvolution'" & key
        ).fetch1("activity_trace")
        fluorescence, fps = (scan.ScanInfo * imaging.Fluorescence.Trace & key).fetch1(
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

        trace_fig.update_layout(get_tracelayout(key))

        self.insert1({**key, "activity_trace": trace_fig.to_json()})


def main(usedb=False):
    motioncorrection_dropdown = wg.Dropdown(
        options=imaging.Segmentation.fetch("KEY"),
        description="Result:",
        description_tooltip='Press "Load" to visualize the cells identified.',
        disabled=False,
        layout=wg.Layout(
            width="95%",
            display="flex",
            flex_flow="row",
            justify_content="space-between",
            grid_area="motioncorrection_dropdown",
        ),
        style={"description_width": "80px"},
    )

    load_button = wg.Button(
        description="Load Image",
        tooltip="Load the average image.",
        layout=wg.Layout(width="120px", grid_area="load_button"),
    )

    FIG1_WIDTH = 600
    FIG1_LAYOUT = go.Layout(
        margin=dict(l=0, r=40, b=0, t=65, pad=0),
        width=FIG1_WIDTH,
        height=600,  # 700,
        transition={"duration": 0},
        title={
            "text": "Average Image with Cells",
            "xanchor": "center",
            "yanchor": "top",
            "y": 0.97,
            "x": 0.5,
        },
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
        modebar_remove=[
            "zoom",
            "resetScale",
            "pan",
            "select",
            "zoomIn",
            "zoomOut",
            "autoScale2d",
        ],
        shapes=[
            go.layout.Shape(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0.035,
                y0=0,
                x1=0.965,
                y1=1.0,
                line={"width": 1, "color": "black"},
            )
        ],
    )
    fig1 = go.Figure(
        go.Image(
            z=None,
            hovertemplate="x: %{x} <br>y: %{y} <br>mask_id: %{customdata} <extra></extra>",
            customdata=None,
        ),
        layout=FIG1_LAYOUT,
    )

    FIG2_WIDTH = 600
    FIG2_HEIGHT = 600
    fig2_layout = get_tracelayout(None, width=FIG2_WIDTH, height=FIG2_HEIGHT)

    fig2 = go.Figure(
        [
            go.Scatter(
                x=None,
                y=None,
                name="Fluorescence",
                yaxis="y1",
            ),
            go.Scatter(x=None, y=None, name="Calcium Event", yaxis="y2"),
        ],
        layout=fig2_layout,
    )

    fig1_widget = go.FigureWidget(fig1)
    fig2_widget = go.FigureWidget(fig2)

    def tooltip_click(trace, points, selector):
        mask_id = trace.customdata[points.ys[0]][points.xs[0]]

        if mask_id > -1:
            activity_trace_figobj = from_json(
                (
                    ActivityReport
                    & motioncorrection_dropdown.value
                    & f"mask='{mask_id}'"
                    # & f"activity_type='z_score'"
                ).fetch1("activity_trace")
            )

            with fig2_widget.batch_update():
                fig2_widget.data[0].x = activity_trace_figobj.data[0].x
                fig2_widget.data[0].y = activity_trace_figobj.data[0].y
                fig2_widget.data[0].name = activity_trace_figobj.data[0].name
                fig2_widget.data[1].x = activity_trace_figobj.data[1].x
                fig2_widget.data[1].y = activity_trace_figobj.data[1].y
                fig2_widget.data[1].name = activity_trace_figobj.data[1].name
                fig2_widget.layout["title"] = {
                    "text": f"Trace for Cell {mask_id}",
                    "xanchor": "center",
                    "yanchor": "top",
                    "y": 0.97,
                    "x": 0.5,
                }

    def response(change, usedb=False):
        if usedb:
            composite_average_image = from_json(
                (ScanLevelReport & motioncorrection_dropdown.value).fetch1(
                    "average_image"
                )
            )

            with fig1_widget.batch_update():
                fig1_widget.data[0].z = composite_average_image.data[0].z
                fig1_widget.data[0].customdata = composite_average_image.data[
                    0
                ].customdata

                fig2_widget.data[0].x = None
                fig2_widget.data[0].y = None
                fig2_widget.data[1].x = None
                fig2_widget.data[1].y = None
        else:
            image = (
                imaging.MotionCorrection.Summary & motioncorrection_dropdown.value
            ).fetch1("average_image")

            cell_mask_ids, mask_xpix, mask_ypix = (
                imaging.Segmentation.Mask * imaging.MaskClassification.MaskType
                & motioncorrection_dropdown.value
            ).fetch("mask", "mask_xpix", "mask_ypix")

            background_image = single_to_3channel_image(image, 1, 99)

            background_image_with_cells_painted = paint_rois(
                background_image, mask_xpix, mask_ypix
            )
            cells_maskid_image = make_maskid_image(
                background_image[:, :, 0], cell_mask_ids, mask_xpix, mask_ypix
            )
            background_with_cells = alpha_combine_2images(
                background_image, background_image_with_cells_painted
            )
            with fig1_widget.batch_update():
                fig1_widget.data[0].z = background_with_cells
                fig1_widget.data[0].customdata = cells_maskid_image

                fig2_widget.layout.title = {
                    "text": "Trace",
                    "xanchor": "center",
                    "yanchor": "top",
                    "y": 0.97,
                    "x": 0.5,
                }
                fig2_widget.data[0].x = None
                fig2_widget.data[0].y = None
                fig2_widget.data[1].x = None
                fig2_widget.data[1].y = None

    fig1_widget.data[0].on_click(tooltip_click)
    load_button.on_click(partial(response, usedb=usedb))

    return wg.VBox(
        [
            wg.HBox(
                [motioncorrection_dropdown, load_button],
                layout=wg.Layout(width=f"{FIG1_WIDTH+FIG2_WIDTH}px"),
            ),
            wg.HBox([fig1_widget, fig2_widget]),
        ]
    )
