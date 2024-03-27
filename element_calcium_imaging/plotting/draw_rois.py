import yaml
import datajoint as dj
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import no_update
from dash_extensions.enrich import (
    DashProxy,
    Input,
    Output,
    State,
    html,
    dcc,
    Serverside,
    ServersideOutputTransform,
)
from scipy import ndimage
from skimage import draw, measure
from tifffile import TiffFile

from .utilities import *


logger = dj.logger


def draw_rois(db_prefix: str):
    imaging = dj.create_virtual_module("imaging", f"{db_prefix}imaging")
    all_keys = (imaging.MotionCorrection).fetch("KEY")

    colors = {"background": "#111111", "text": "#00a0df"}

    app = DashProxy(transforms=[ServersideOutputTransform()])
    app.layout = html.Div(
        [
            html.H2("Draw ROIs", style={"color": colors["text"]}),
            html.Label("Select data key from dropdown", style={"color": colors["text"]}),
            dcc.Dropdown(
                id="toplevel-dropdown", options=[str(key) for key in all_keys]
            ),
            html.Br(),
            html.Div(
                [
                    html.Button("Load Image", id="load-image-button", style={"margin-right": "20px"}),
                    dcc.RadioItems(
                        id='image-type-radio',
                        options=[
                            {'label': 'Average Image', 'value': 'average_image'},
                            {'label': 'Max Projection Image', 'value': 'max_projection_image'}
                        ],
                        value='average_image',  # Default value
                        labelStyle={'display': 'inline-block', 'margin-right': '10px'},  # Inline display with some margin
                        style={'display': 'inline-block', 'color': colors['text']}  # Inline display to keep it on the same line
                    ),
                    html.Div(
                        [
                            html.Button("Submit Curated Masks", id="submit-button"),
                        ],
                        style={"textAlign": "right", "flex": "1", "display": "inline-block"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "flex-start",
                    "align-items": "center",
                },
            ),
            html.Br(),
            html.Br(),
            html.Div(
                [
                    dcc.Graph(
                        id="avg-image",
                        config={
                            "modeBarButtonsToAdd": [
                                "drawclosedpath",
                                "drawrect",
                                "drawcircle",
                                "eraseshape",
                            ],
                        },
                        style={"width": "100%", "height": "100%"},
                    )
                ],
                style={
                    "display": "flex",
                    "justify-content": "center",  # Centers the child horizontally
                    "align-items": "center",  # Centers the child vertically (if you have vertical space to work with)
                    "padding": "0.0",
                    "margin": "auto"  # Automatically adjust the margins to center the div
                },
            ),
            html.Pre(id="annotations"),
            html.Div(id="button-output"),
            dcc.Store(id="store-key"),
            dcc.Store(id="store-mask"),
            dcc.Store(id="store-movie"),
            html.Div(id="submit-output"),
        ]
    )

    @app.callback(
        Output("store-key", "value"),
        Input("toplevel-dropdown", "value"),
    )
    def store_key(value):
        if value is not None:
            return Serverside(value)
        else:
            return no_update

    @app.callback(
        Output("avg-image", "figure"),
        Output("store-movie", "average_images"),
        State("store-key", "value"),
        Input("load-image-button", "n_clicks"),
        Input("image-type-radio", "value"),
        prevent_initial_call=True,
    )
    def create_figure(value, render_n_clicks, image_type):
        if render_n_clicks is not None:
            if image_type == "average_image":
                summary_images = (imaging.MotionCorrection.Summary & yaml.safe_load(value)).fetch("average_image")
            else:
                summary_images = (imaging.MotionCorrection.Summary & yaml.safe_load(value)).fetch("max_proj_image")
            average_images = [image.astype("float") for image in summary_images]
            roi_contours = get_contours(yaml.safe_load(value), db_prefix)
            logger.info("Generating figure.")
            fig = px.imshow(np.asarray(average_images), animation_frame=0, binary_string=True, labels=dict(animation_frame="plane"))
            for contour in roi_contours:
                # Note: contour[:, 1] are x-coordinates, contour[:, 0] are y-coordinates
                fig.add_trace(
                    go.Scatter(
                        x=contour[:, 1],  # Plotly uses x, y order for coordinates
                        y=contour[:, 0],
                        mode="lines",  # Display as lines (not markers)
                        line=dict(color="white", width=0.5),  # Set line color and width
                        showlegend=False,  # Do not show legend for each contour
                    )
                )
            fig.update_layout(
                dragmode="drawrect",
                autosize=True,
                height=550,
                newshape=dict(opacity=0.6, fillcolor="#00a0df"),
                plot_bgcolor=colors["background"],
                paper_bgcolor=colors["background"],
                font_color=colors["text"],
            )
            fig.update_annotations(bgcolor="#00a0df")
        else:
            return no_update
        return fig, Serverside(average_images)

    @app.callback(
        Output("store-mask", "annotation_list"),
        Input("avg-image", "relayoutData"),
        prevent_initial_call=True,
    )
    def on_relayout(relayout_data):
        if not relayout_data:
            return no_update
        else:
            if "shapes" in relayout_data:
                global shape_type
                try:
                    shape_type = relayout_data["shapes"][-1]["type"]
                    return Serverside(relayout_data)
                except IndexError:
                    return no_update
            elif any(["shapes" in key for key in relayout_data]):
                return Serverside(relayout_data)


    @app.callback(
        Output("submit-output", "children"),
        Input("submit-button", "n_clicks"),
        State("store-mask", "annotation_list"),
        State("store-key", "value")
    )
    def submit_annotations(n_clicks, annotation_list, value):
        print("submitting annotations")
        x_mask_li = []
        y_mask_li = []
        if n_clicks is not None:
            if "shapes" in annotation_list:
                shapes = [d["type"] for d in annotation_list["shapes"]]
                for shape, annotation in zip(shapes, annotation_list["shapes"]):
                    mask = create_mask(annotation, shape)
                    y_mask_li.append(mask[0])
                    x_mask_li.append(mask[1])
                
            suite2p_masks = convert_masks_to_suite2p_format(
                [np.array([x_mask_li, y_mask_li])], (512, 512)
            )
            fluo_traces = extract_signals_suite2p(yaml.safe_load(value), suite2p_masks)

        else:
            return no_update

    app.run_server(port=8000)
