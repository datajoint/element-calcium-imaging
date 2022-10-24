import plotly.graph_objects as go
import cv2
import numpy as np


def single_to_3channel_image(image, low_q=0, high_q=99.9):
    image = (image - image.min()) ** 0.5
    low_p, high_p = np.percentile(image, [low_q, high_q])
    image = np.uint8(255 * (image - low_p) / (high_p - low_p))
    return np.dstack([image] * 3)


def paint_rois(image, mask_xpix, mask_ypix):
    SATURATION = 40
    VALUE = 255

    # Assign colors to each region
    masks = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    for xpix, ypix in zip(mask_xpix, mask_ypix):
        masks[ypix, xpix] = [np.random.random()*255, SATURATION, VALUE]
    return np.uint8(cv2.cvtColor(masks.astype(np.float32), cv2.COLOR_HSV2RGB))



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


def plot_cell_overlayed_image(imaging, segmentation_key):

    average_image = (imaging.MotionCorrection.Summary & segmentation_key).fetch1("average_image")


    cell_mask_ids, mask_xpix, mask_ypix = (
        imaging.Segmentation.Mask * imaging.MaskClassification.MaskType & segmentation_key
    ).fetch("mask", "mask_xpix", "mask_ypix")

    background_image = single_to_3channel_image(average_image, low_q=0, high_q=99.9)

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

    return image_fig


def plot_cell_traces(imaging, cell_key):
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
    