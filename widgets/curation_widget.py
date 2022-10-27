import cv2
import numpy as np
import datajoint as dj
from matplotlib import colors
import plotly.graph_objects as go
from ipywidgets import widgets as wg
from plotly.subplots import make_subplots


check_list, trace_list = [], []


def mask_overlayed_image(
    image, mask_xpix, mask_ypix, cell_mask_ids, low_q=0, high_q=99.9
):
    q_min, q_max = np.quantile(image, [low_q, high_q])
    image = np.clip(image, q_min, q_max)
    image = (image - q_min) / (q_max - q_min)

    SATURATION = 0.7
    image = image[:, :, None] * np.array([0, 0, 1])
    maskid_image = np.full(image.shape[:2], -1)
    for xpix, ypix, roi_id in zip(mask_xpix, mask_ypix, cell_mask_ids):
        image[ypix, xpix, :2] = [np.random.rand(), SATURATION]
        maskid_image[ypix, xpix] = roi_id
    return colors.hsv_to_rgb(image), maskid_image


def main(db_prefix):
    imaging = dj.create_virtual_module("imaging", f"{db_prefix}imaging")
    Processing = imaging.Processing
    MotionCorrection = imaging.MotionCorrection
    Segmentation = imaging.Segmentation
    MaskClassification = imaging.MaskClassification

    title_button = wg.Button(
        description="Calcium Imaging Curator",
        button_style="info",
        layout=wg.Layout(
            height="auto", width="auto", grid_area="title_button", border="solid"
        ),
        style=wg.ButtonStyle(button_color="blue"),
        disabled=True,
    )
    processed_dropdown = wg.Dropdown(
        options=Processing.fetch("KEY"),
        description="Result:",
        description_tooltip='Press "Load" to visualize the ROI classification results.',
        disabled=False,
        layout=wg.Layout(
            width="95%",
            display="flex",
            flex_flow="row",
            justify_content="space-between",
            grid_area="processed_dropdown",
        ),
        style={"description_width": "80px"},
    )

    select_background = wg.Dropdown(
        options=[("Average Image", "average_image")],
        value="average_image",
        description="Background:",
        tooltips="Background Image",
        disabled=False,
        layout=wg.Layout(width="40%", grid_area="select_background"),
        style={"description_width": "80px"},
    )

    manual_entry_textarea = wg.Text(
        description="MaskId:",
        description_tooltip='Enter a MaskId and press "Add/Remove" to commit the request.',
        disabled=False,
        continuous_update=True,
        layout=wg.Layout(width="150px", grid_area="manual_entry_textarea"),
        style={"description_width": "70px"},
    )

    load_button = wg.Button(
        description="Load Images",
        tooltip="Load the ROI classification results.",
        layout=wg.Layout(width="auto", grid_area="load_button"),
    )
    submit_button = wg.Button(
        description="Submit",
        tooltip="Apply the curation request below. Note that the changes made here are irrversible!",
        layout=wg.Layout(width="auto", grid_area="submit_button"),
        icon="paper-plane-o",
    )
    clear_button = wg.Button(
        description="Clear All",
        tooltip="Clear the curation request below (e.g. to start over).",
        layout=wg.Layout(width="auto", grid_area="clear_button"),
        icon="trash-o",
    )

    add_remove_button = wg.Button(
        description="Add/Remove",
        layout=wg.Layout(width="auto", grid_area="add_remove_button"),
    )

    data = (
        go.Image(z=None, hovertemplate=None, customdata=None),
        go.Image(z=None, hovertemplate=None, customdata=None),
    )

    fig = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.01,
        vertical_spacing=0,
        column_titles=["Cells", "NonCells"],
    )

    fig.layout.xaxis2.update({"matches": "x"})
    fig.add_traces(data, rows=[1, 1], cols=[1, 2])
    fig["layout"].update(
        margin=dict(l=0, r=0, b=0, t=0, pad=0),
        xaxis={"title": "", "visible": False, "showticklabels": False},
        yaxis={"title": "", "visible": False, "showticklabels": False},
        xaxis2={"title": "", "visible": False, "showticklabels": False},
        yaxis2={"title": "", "visible": False, "showticklabels": False},
        transition={"duration": 0},
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
    fwg = go.FigureWidget(fig)

    def response(change):
        global check_list, trace_list
        check_list, trace_list = [], []

        image = (MotionCorrection.Summary & processed_dropdown.value).fetch1(
            "average_image"
        )

        # Cells
        cell_mask_ids, mask_xpix, mask_ypix = (
            Segmentation.Mask * MaskClassification.MaskType & processed_dropdown.value
        ).fetch("mask", "mask_xpix", "mask_ypix")

        background_image_with_cells_painted, cells_maskid_image = mask_overlayed_image(
            image, mask_xpix, mask_ypix, cell_mask_ids, low_q=0, high_q=99.9
        )

        # NonCells
        noncell_mask_ids, mask_xpix, mask_ypix = (
            (Segmentation.Mask - MaskClassification.MaskType) & processed_dropdown.value
        ).fetch("mask", "mask_xpix", "mask_ypix")

        (
            background_image_with_noncells_paints,
            noncells_maskid_image,
        ) = mask_overlayed_image(
            image, mask_xpix, mask_ypix, noncell_mask_ids, low_q=0, high_q=99.9
        )

        # Update plotly figure
        with fwg.batch_update():
            fwg.data[0].z = background_image_with_cells_painted
            fwg.data[1].z = background_image_with_noncells_paints

            fwg.data[0].customdata = cells_maskid_image
            fwg.data[1].customdata = noncells_maskid_image
            fwg.data[0].hovertemplate = "x: %{x} <br>y: %{y} <br>mask_id: %{customdata}"
            fwg.data[1].hovertemplate = "x: %{x} <br>y: %{y} <br>mask_id: %{customdata}"

            # Clear roi list when the Calcium imaging result shown changes.
            clear_selected_rois(None)

    figure_output = wg.VBox(
        [fwg], layout=wg.Layout(width="95%", grid_area="figure_output")
    )
    figure_output.add_class("box_style")

    text_output = wg.Output(
        layout=wg.Layout(
            width="auto",
            grid_area="text_output",
            border="1px solid black",
            overflow_y="auto",
            height=figure_output.layout.height,
        )
    )

    def tooltip_click(trace, points, selector):
        global check_list, trace_list
        mask_id = trace.customdata[points.ys, points.xs]

        if mask_id >= 0 and mask_id not in check_list:
            mask_id = mask_id[0]
            check_list.append(mask_id)

            trace_list.append(points.trace_index)

            text_output.clear_output()
            with text_output:
                print("MaskId     Change")
                print("------ ---------------")
                for i, trace_id in zip(check_list, trace_list):
                    trace_id_map = "NonCell->Cell" if trace_id else "Cell->NonCell"
                    print(f"%6i %15s" % (i, trace_id_map))

    def clear_selected_rois(change):
        global check_list, trace_list
        check_list, trace_list = [], []

        text_output.clear_output()
        with text_output:
            print("MaskId     Change")
            print("------ ---------------")

    def text_response(change):
        global check_list, trace_list

        entry = manual_entry_textarea.value

        if (
            entry.isnumeric()
            and fwg.data[0].z is not None
            and int(entry)
            <= max(fwg.data[0].customdata.max(), fwg.data[1].customdata.max())
        ):
            entry = int(manual_entry_textarea.value)

            trace_id = 0 if entry in fwg.data[0].customdata else 1

            if entry not in check_list:
                check_list.append(entry)
                trace_list.append(trace_id)
            elif entry in check_list:
                index = check_list.index(entry)
                check_list.remove(entry)
                del trace_list[index]

            text_output.clear_output()
            with text_output:
                print("MaskId Roi Type Change")
                print("------ ---------------")
                for i, trace_id in zip(check_list, trace_list):
                    trace_id_map = "NonCell->Cell" if trace_id else "Cell->NonCell"
                    print(f"%6i %15s" % (i, trace_id_map))

    def submit_click(change):
        global check_list, trace_list

        cell_to_noncell = []
        noncell_to_cell = []

        if len(check_list) > 0:
            for trace, mask_id in zip(trace_list, check_list):
                if trace == 0:
                    cell_to_noncell.append(mask_id)
                elif trace == 1:
                    noncell_to_cell.append(mask_id)
                else:
                    print("Unknown Trace")

            mask_classification_key = (
                MaskClassification & processed_dropdown.value
            ).fetch1("KEY")

            delete_activity = False
            with dj.config(safemode=False):
                with dj.conn.connection.transaction:
                    if len(cell_to_noncell) > 0:
                        (
                            MaskClassification.MaskType
                            & processed_dropdown.value
                            & [f"mask={x}" for x in cell_to_noncell]
                        ).delete(force=True)
                        delete_activity = True
                    if len(noncell_to_cell) > 0:
                        mask_entries = (
                            (
                                Segmentation.Mask.proj()
                                & processed_dropdown.value
                                & [f"mask={x}" for x in noncell_to_cell]
                            )
                            .proj(
                                mask_classification_method=f'"{mask_classification_key["mask_classification_method"]}"',
                                mask_type='"soma"',
                                confidence="1.0",
                            )
                            .fetch(as_dict=True)
                        )
                        MaskClassification.Masktype.insert(mask_entries)
                        delete_activity = True
                    if delete_activity:
                        (imaging.Activity & processed_dropdown.value).delete(
                            forece=True
                        )

                    with text_output:
                        print("Curation completed!")

    fwg.data[0].on_click(tooltip_click)
    fwg.data[1].on_click(tooltip_click)

    load_button.on_click(response)
    clear_button.on_click(clear_selected_rois)
    manual_entry_textarea.on_submit(text_response)
    submit_button.on_click(submit_click)
    add_remove_button.on_click(text_response)

    main_container = wg.GridBox(
        children=[
            title_button,
            processed_dropdown,
            select_background,
            load_button,
            submit_button,
            clear_button,
            add_remove_button,
            figure_output,
            text_output,
            manual_entry_textarea,
        ],
        layout=wg.Layout(
            grid_template_areas="""
            "title_button title_button title_button title_button title_button"
            "processed_dropdown manual_entry_textarea .  load_button submit_button"
            "select_background . .  add_remove_button clear_button "
            "figure_output figure_output figure_output text_output text_output"
            """
        ),
        grid_template_rows="auto auto auto auto",
        grid_template_columns="71% 7% 2% 10% 10%",
    )

    return main_container
