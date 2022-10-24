from functools import partial
from ipywidgets import widgets as wg

from . import cell_plot


def main(imaging, usedb=False):
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
    fig2_layout = cell_plot.get_tracelayout(None, width=FIG2_WIDTH, height=FIG2_HEIGHT)


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
                    TraceReport
                    & motioncorrection_dropdown.value
                    & f"mask='{mask_id}'"
                ).fetch1("cell_traces")
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
            cell_overlayed_image = from_json(
                (ScanLevelReport & motioncorrection_dropdown.value).fetch1(
                    "cell_overlayed_image"
                )
            )

            with fig1_widget.batch_update():
                fig1_widget.data[0].z = cell_overlayed_image.data[0].z
                fig1_widget.data[0].customdata = cell_overlayed_image.data[0].customdata


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

            background_image = cell_plot.single_to_3channel_image(image, low_q=0, high_q=99.9)


            background_image_with_cells_painted = cell_plot.paint_rois(

                background_image, mask_xpix, mask_ypix
            )
            cells_maskid_image = cell_plot.make_maskid_image(

                background_image[:, :, 0], cell_mask_ids, mask_xpix, mask_ypix
            )
            background_with_cells = cell_plot.alpha_combine_2images(

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
