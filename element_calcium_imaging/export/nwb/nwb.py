import pathlib

import numpy as np
import datajoint as dj
from datajoint import DataJointError
from element_interface.utils import find_full_path
from neuroconv import ConverterPipe
from pynwb import NWBHDF5IO, NWBFile
from pynwb.ophys import (
    Fluorescence,
    ImageSegmentation,
    OpticalChannel,
    RoiResponseSeries,
    TwoPhotonSeries,
)

from ... import scan
from ... import imaging_no_curation
from ...scan import get_calcium_imaging_files, get_imaging_root_data_dir

logger = dj.logger

if imaging_no_curation.schema.is_activated():
    imaging = imaging_no_curation
else:
    raise DataJointError(
        "This export function is designed for the `imaging_no_curation` module."
    )


def imaging_session_to_nwb(
    session_key,
    save_path=None,
    include_raw_data=False,
    lab_key=None,
    project_key=None,
    protocol_key=None,
    nwbfile_kwargs=None,
):
    session_to_nwb = getattr(imaging._linking_module, "session_to_nwb", False)

    if not save_path:
        output_relative_dir = (imaging.ProcessingTask & session_key).fetch1(
            "processing_output_dir"
        )
        save_path = find_full_path(get_imaging_root_data_dir(), output_relative_dir)

    if session_to_nwb:
        nwb_file = session_to_nwb(
            session_key,
            lab_key=lab_key,
            project_key=project_key,
            protocol_key=protocol_key,
            additional_nwbfile_kwargs=nwbfile_kwargs,
        )
    else:
        nwb_file = NWBFile(**nwbfile_kwargs)
    if include_raw_data:
        _create_raw_data_nwbfile(session_key, linked_nwb_file=nwb_file)
    else:
        imaging_plane = _add_scan_to_nwb(session_key, nwbfile=nwb_file)
        _add_image_series_to_nwb(session_key, imaging_plane=imaging_plane)
        _add_segmentation_data_to_nwb(
            session_key, nwbfile=nwb_file, imaging_plane=imaging_plane
        )

    return nwb_file


def _create_raw_data_nwbfile(session_key, linked_nwb_file):
    acquisition_software = (scan.Scan & session_key).fetch1("acq_software")
    frame_rate = (scan.ScanInfo & session_key).fetch1("fps")

    if acquisition_software == "NIS":
        raise NotImplementedError(
            "Packaging raw data acquired from `Nikon NIS Elements` software is not supported at this time."
        )

    elif acquisition_software == "PrairieView":
        n_planes = (scan.ScanInfo & session_key).fetch1("ndepths")
        if n_planes > 1:
            from neuroconv.converters import (
                BrukerTiffMultiPlaneConverter as BrukerTiffConverter,
            )
        else:
            from neuroconv.converters import (
                BrukerTiffSinglePlaneConverter as BrukerTiffConverter,
            )
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )

        imaging_interface = BrukerTiffConverter(
            file_path=raw_data_files_location[0],
            fallback_sampling_frequency=frame_rate,
        )
        metadata = imaging_interface.get_metadata()
        imaging_interface.run_conversion(
            nwbfile=linked_nwb_file,
            metadata=metadata,
        )
    else:
        if acquisition_software == "ScanImage":
            from neuroconv.datainterfaces import (
                ScanImageImagingInterface as ImagingInterface,
            )
        elif acquisition_software == "Scanbox":
            from neuroconv.datainterfaces import SbxImagingInterface as ImagingInterface

        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )

        imaging_interface = ImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        metadata = imaging_interface.get_metadata()
        imaging_interface.add_to_nwbfile(
            nwbfile=linked_nwb_file,
            metadata=metadata,
        )


def _add_scan_to_nwb(session_key, nwbfile):
    from math import nan

    try:
        scan_key = (scan.Scan & session_key).fetch1("KEY")
    except DataJointError:
        raise NotImplementedError(
            "Exporting more than one scan per session to NWB is not supported yet."
        )

    scanner_name, scan_notes = (scan.Scan & scan_key).fetch1("scanner", "scan_notes")
    device = nwbfile.create_device(
        name=scanner_name if scanner_name is not None else "TwoPhotonMicroscope",
        description="Two photon microscope",
        manufacturer="Microscope manufacturer",
    )

    no_channels, frame_rate = (scan.ScanInfo & scan_key).fetch1("nchannels", "fps")

    field_keys = (scan.ScanInfo.Field & scan_key).fetch("KEY")

    for channel in range(no_channels):
        optical_channel = OpticalChannel(
            name=f"OpticalChannel{channel+1}",
            description=f"Optical channel number {channel+1}",
            emission_lambda=nan,
        )

        for field_key in field_keys:
            field_no = (scan.ScanInfo.Field & field_key).fetch1("field_idx")
            imaging_plane = nwbfile.create_imaging_plane(
                name=f"ImagingPlane{field_no+1}",
                optical_channel=optical_channel,
                imaging_rate=frame_rate,
                description=scan_notes
                if scan_notes != ""
                else f"Imaging plane for channel {channel+1}",
                device=device,
                excitation_lambda=nan,
                indicator="unknown",
                location="unknown",
                grid_spacing=(0.01, 0.01),
                grid_spacing_unit="meters",
                origin_coords=[1.0, 2.0, 3.0],
                origin_coords_unit="meters",
            )
    return imaging_plane


def _add_image_series_to_nwb(session_key, imaging_plane):
    imaging_files = (scan.ScanInfo.ScanFile & session_key).fetch("file_path")
    two_p_series = TwoPhotonSeries(
        name="TwoPhotonSeries",
        dimension=(scan.ScanInfo.Field & session_key).fetch1("px_height", "px_width"),
        external_file=imaging_files,
        imaging_plane=imaging_plane,
        starting_frame=[0],
        format="external",
        starting_time=0.0,
        rate=(scan.ScanInfo & session_key).fetch1("fps"),
    )
    return two_p_series


def _add_motion_correction_to_nwb(session_key, nwbfile):
    raise NotImplementedError(
        "Motion Correction data cannot be packaged into NWB at this time."
    )


def _add_segmentation_data_to_nwb(session_key, nwbfile, imaging_plane):
    ophys_module = nwbfile.create_processing_module(
        name="ophys", description="optical physiology processed data"
    )
    img_seg = ImageSegmentation()
    ps = img_seg.create_plane_segmentation(
        name="PlaneSegmentation",
        description="output from segmenting",
        imaging_plane=imaging_plane,
    )
    ophys_module.add(img_seg)

    mask_keys = (imaging.Segmentation.Mask & session_key).fetch("KEY")
    for mask_key in mask_keys:
        ps.add_roi(
            pixel_mask=np.asarray(
                (imaging.Segmentation.Mask() & mask_key).fetch1(
                    "mask_xpix", "mask_ypix", "mask_weights"
                )
            ).T
        )

    rt_region = ps.create_roi_table_region(
        region=((imaging.Segmentation.Mask & session_key).fetch("mask")).tolist(),
        description="All ROIs from database.",
    )

    channels = (scan.ScanInfo & session_key).fetch1("nchannels")
    for channel in range(channels):
        roi_resp_series = RoiResponseSeries(
            name=f"Fluorescence_{channel}",
            data=np.stack(
                (
                    imaging.Fluorescence.Trace
                    & session_key
                    & f"fluo_channel='{channel}'"
                ).fetch("fluorescence")
            ).T,
            rois=rt_region,
            unit="a.u.",
            rate=(scan.ScanInfo & session_key).fetch1("fps"),
        )
        neuropil_series = RoiResponseSeries(
            name=f"Neuropil_{channel}",
            data=np.stack(
                (
                    imaging.Fluorescence.Trace
                    & session_key
                    & f"fluo_channel='{channel}'"
                ).fetch("neuropil_fluorescence")
            ).T,
            rois=rt_region,
            unit="a.u.",
            rate=(scan.ScanInfo & session_key).fetch1("fps"),
        )
        deconvolved_series = RoiResponseSeries(
            name=f"Deconvolved_{channel}",
            data=np.stack(
                (
                    imaging.Activity.Trace & session_key & f"fluo_channel='{channel}'"
                ).fetch("activity_trace")
            ).T,
            rois=rt_region,
            unit="a.u.",
            rate=(scan.ScanInfo & session_key).fetch1("fps"),
        )
    fl = Fluorescence(
        roi_response_series=[roi_resp_series, neuropil_series, deconvolved_series]
    )
    ophys_module.add(fl)


def write_nwb(nwbfile, fname, check_read=True):
    with pynwb.NWBHDF5IO(fname, "w") as io:
        io.write(nwbfile)

    if check_read:
        with pynwb.NWBHDF5IO(fname, "r") as io:
            io.read()
    logger.info("File saved successfully")
