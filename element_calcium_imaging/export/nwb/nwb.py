import pathlib
import datajoint as dj
import numpy as np

from datajoint import DataJointError
from pynwb import NWBHDF5IO, NWBFile
from pynwb.image import ImageSeries
from pynwb.ophys import (
    CorrectedImageStack,
    Fluorescence,
    ImageSegmentation,
    MotionCorrection,
    OnePhotonSeries,
    OpticalChannel,
    RoiResponseSeries,
    TwoPhotonSeries,
)

from ... import imaging, scan
from ...scan import get_imaging_root_data_dir, get_image_files


def add_scan_to_nwb(session_key, nwbfile):
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


def add_data_to_nwb(session_key, nwbfile, raw_data, plane):
    if raw_data:
        from element_interface.utils import find_full_path

        acquisition_software = (scan.Scan & session_key).fetch1("acq_software")
        output_dir = (imaging.ProcessingTask & session_key).fetch1(
            "processing_output_dir"
        )

        save_path = get_imaging_root_data_dir() / pathlib.Path(output_dir)

        if acquisition_software == "ScanImage":
            from neuroconv.datainterfaces import ScanImageImagingInterface

            imaging_data_location = get_image_files(session_key)
            scanimage_interface = ScanImageImagingInterface(
                file_path=imaging_data_location[0],
                fallback_sampling_frequency=(scan.ScanInfo & session_key).fetch1("fps"),
            )
            scanimage_interface.run_conversion(nwbfile_path=(save_path / "nwbfile"))

            with NWBHDF5IO((save_path / "nwbfile"), "r+") as io:
                nwbfile = io.read()

            # frame_rate = (scan.ScanInfo & session_key).fetch1("fps")
            # two_p_series = TwoPhotonSeries(
            #     name="TwoPhotonSeries",
            #     data=imaging_data,
            #     imaging_plane=plane,
            #     rate=frame_rate,
            #     unit="raw fluorescence",
            # )
        elif acquisition_software == "PrairieView":
            from neuroconv.datainterfaces import BrukerTiffImagingInterface

            imaging_data_location = get_image_files(session_key)
            for file in imaging_data_location:
                bruker_tiff_interface = BrukerTiffImagingInterface(
                    file_path=file,
                    fallback_sampling_frequency=(scan.ScanInfo & session_key).fetch1(
                        "fps"
                    ),
                )
            bruker_tiff_interface.run_conversion(nwbfile_path=(save_path / "nwbfile"))

        elif acquisition_software == "Scanbox":
            from neuroconv.datainterfaces import SbxImagingInterface

            imaging_data_location = get_image_files(session_key)
            sbx_interface = SbxImagingInterface(
                file_path=imaging_data_location[0],
                fallback_sampling_frequency=(scan.ScanInfo & session_key).fetch1("fps"),
            )
            sbx_interface.run_conversion(nwbfile_path=(save_path / "nwbfile"))
        elif acquisition_software == "NIS":
            raise NotImplementedError(
                "Exporting raw data from .nd2 files to NWB files is not supported yet. Please set `raw=False` and try again."
            )

    else:
        imaging_files = (scan.ScanInfo.ScanFile & session_key).fetch("file_path")
        two_p_series = TwoPhotonSeries(
            name="TwoPhotonSeries",
            dimension=(scan.ScanInfo.Field & session_key).fetch1(
                "px_height", "px_width"
            ),
            external_file=imaging_files,
            imaging_plane=plane,
            starting_frame=[0],
            format="external",
            starting_time=0.0,
            rate=(scan.ScanInfo & session_key).fetch1("fps"),
        )


def add_motion_correction_to_nwb(session_key, nwbfile):
    raise NotImplementedError(
        "Motion Correction data cannot be packaged into NWB at this time."
    )


def add_segmentation_data_to_nwb(session_key, nwbfile, plane):
    ophys_module = nwbfile.create_processing_module(
        name="ophys", description="optical physiology processed data"
    )
    img_seg = ImageSegmentation()
    ps = img_seg.create_plane_segmentation(
        name="PlaneSegmentation",
        description="output from segmenting",
        imaging_plane=plane,
    )
    ophys_module.add(img_seg)

    mask_keys = (imaging.Segmentation.Mask & session_key).fetch("KEY")
    for mask_key in mask_keys:
        ps.add_roi(
            image_mask=np.asarray(
                (imaging.Segmentation.Mask() & mask_key).fetch1(
                    "mask_xpix", "mask_ypix", "mask_weights"
                )
            )
        )

    rt_region = ps.create_roi_table_region(
        region=((imaging.Segmentation.Mask & session_key).fetch("mask")).tolist(),
        description="All ROIs from database.",
    )

    channels = (scan.ScanInfo & session_key).fetch1("nchannels")
    for channel in range(channels):
        roi_resp_series = RoiResponseSeries(
            name=f"RoiFluorescenceSeries{channel}",
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
    fl = Fluorescence(roi_response_series=roi_resp_series)
    ophys_module.add(fl)


def imaging_session_to_nwb(
    session_key,
    raw=False,
    lab_key=None,
    project_key=None,
    protocol_key=None,
    nwbfile_kwargs=None,
):
    session_to_nwb = getattr(imaging._linking_module, "session_to_nwb", False)

    if session_to_nwb:
        nwbfile = session_to_nwb(
            session_key,
            lab_key=lab_key,
            project_key=project_key,
            protocol_key=protocol_key,
            additional_nwbfile_kwargs=nwbfile_kwargs,
        )
    else:
        nwbfile = NWBFile(**nwbfile_kwargs)

    imaging_plane = add_scan_to_nwb(session_key, nwbfile)
    add_data_to_nwb(session_key, nwbfile, raw_data=raw, plane=imaging_plane)
    add_segmentation_data_to_nwb(session_key, nwbfile, imaging_plane)

    return nwbfile
