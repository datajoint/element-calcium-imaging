import pathlib
import datajoint as dj
import numpy as np

from datajoint import DataJointError
from element_interface.utils import find_full_path
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
from neuroconv import ConverterPipe

from ... import imaging, scan
from ...scan import get_imaging_root_data_dir, get_image_files


def create_raw_data_nwbfile(session_key, output_directory, nwb_path):

    acquisition_software = (scan.Scan & session_key).fetch1("acq_software")
    session_paramset_key = (imaging.ProcessingTask & session_key).fetch1("paramset_idx")
    processing_method = (
        imaging.ProcessingParamSet & f"paramset_idx='{session_paramset_key}'"
    ).fetch1("processing_method")

    if acquisition_software == "ScanImage" and processing_method == "suite2p":
        from neuroconv.datainterfaces import (
            ScanImageImagingInterface,
            Suite2pSegmentationInterface,
        )

        processing_folder_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_image_files(session_key, "*.tif")
        scan_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        s2p_interface = Suite2pSegmentationInterface(
            folder_path=processing_folder_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, s2p_interface])

    elif acquisition_software == "ScanImage" and processing_method == "CaImAn":
        from neuroconv.datainterfaces import (
            ScanImageImagingInterface,
            CaimanSegmentationInterface,
        )

        caiman_hdf5 = list(processing_folder_location.rglob("caiman_analysis.hdf5"))
        scan_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        caiman_interface = CaimanSegmentationInterface(file_path=caiman_hdf5[0])
        converter = ConverterPipe(data_interfaces=[scan_interface, caiman_interface])

    elif acquisition_software == "ScanImage" and processing_method == "extract":
        from neuroconv.datainterfaces import (
            ScanImageImagingInterface,
            ExtractSegmentationInterface,
        )

        processing_file_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_image_files(session_key, "*.tif")
        scan_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        extract_interface = ExtractSegmentationInterface(
            file_path=processing_file_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, extract_interface])

    elif acquisition_software == "Scanbox" and processing_method == "suite2p":
        from neuroconv.datainterfaces import (
            SbxImagingInterface,
            Suite2pSegmentationInterface,
        )

        scan_interface = SbxImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        s2p_interface = Suite2pSegmentationInterface(
            folder_path=processing_folder_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, s2p_interface])

    elif acquisition_software == "Scanbox" and processing_method == "CaImAn":
        from neuroconv.datainterfaces import (
            SbxImagingInterface,
            CaimanSegmentationInterface,
        )

        caiman_hdf5 = list(processing_folder_location.rglob("caiman_analysis.hdf5"))
        scan_interface = SbxImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        caiman_interface = CaimanSegmentationInterface(file_path=caiman_hdf5[0])
        converter = ConverterPipe(data_interfaces=[scan_interface, caiman_interface])
    
    elif acquisition_software == "Scanbox" and processing_method == "extract":
        from neuroconv.datainterfaces import (
            SbxImagingInterface,
            ExtractSegmentationInterface,
        )

        processing_file_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_image_files(session_key, "*.tif")
        scan_interface = SbxImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        extract_interface = ExtractSegmentationInterface(
            file_path=processing_file_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, extract_interface])
    
    elif acquisition_software == "PrairieView" and processing_method == "suite2p":
        n_planes = (scan.ScanInfo & session_key).fetch1("ndepths")
        if n_planes > 1:
            from neuroconv.datainterfaces import BrukerTiffMultiPlaneConverter as BrukerTiffConverter
        else:
            from neuroconv.datainterfaces import BrukerTiffSinglePlaneConverter as BrukerTiffConverter
        from neuroconv.datainterfaces import Suite2pSegmentationInterface

        processing_folder_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_image_files(session_key, "*.tif")
        bruker_interface = BrukerTiffConverter(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=30
        )
        s2p_interface = Suite2pSegmentationInterface(
            folder_path=processing_folder_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, s2p_interface])

    metadata = converter.get_metadata()
    metadata["NWBFile"].update(session_description="DataJoint Session")
    converter.run_conversion(nwbfile_path=(nwb_path / f'{session_key["subject"]}_nwbfile'), metadata=metadata)


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


def add_image_series_to_nwb(session_key, imaging_plane):
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


def add_motion_correction_to_nwb(session_key, nwbfile):
    raise NotImplementedError(
        "Motion Correction data cannot be packaged into NWB at this time."
    )


def add_segmentation_data_to_nwb(session_key, nwbfile, imaging_plane):
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
        neuorpil_series = RoiResponseSeries(
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
                    imaging.Activity.Trace
                    & session_key
                    & f"fluo_channel='{channel}'"
                ).fetch("activity_trace")
            ).T,
            rois=rt_region,
            unit="a.u.",
            rate=(scan.ScanInfo & session_key).fetch1("fps"),
        )
    fl = Fluorescence(roi_response_series=[roi_resp_series, neuorpil_series, deconvolved_series])
    ophys_module.add(fl)


def imaging_session_to_nwb(
    session_key,
    save_path=None,
    include_raw_data=False,
    processed_data_source="database" or "filesystem",
    lab_key=None,
    project_key=None,
    protocol_key=None,
    nwbfile_kwargs=None,
):
    session_to_nwb = getattr(imaging._linking_module, "session_to_nwb", False)

    output_relative_dir = (imaging.ProcessingTask & session_key).fetch1(
        "processing_output_dir"
    )
    output_dir = find_full_path(get_imaging_root_data_dir(), output_relative_dir)

    if not save_path:
        output_relative_dir = (imaging.ProcessingTask & session_key).fetch1(
            "processing_output_dir"
        )
        save_path = find_full_path(get_imaging_root_data_dir(), output_relative_dir)

    if include_raw_data:
        create_raw_data_nwbfile(session_key, output_directory=output_dir, nwb_path=save_path)
        with NWBHDF5IO((save_path / f'{session_key["subject"]}_nwbfile'), mode="r+") as io:
            nwb_file = io.read()
            if session_to_nwb:
                nwb_file = session_to_nwb(
                    session_key,
                    lab_key=lab_key,
                    project_key=project_key,
                    protocol_key=protocol_key,
                    additional_nwbfile_kwargs=nwbfile_kwargs,
                )
                io.write(nwb_file)
            else:
                if "Subject" in nwbfile_kwargs:
                    from pynwb.file import Subject
                    nwb_file.subject = Subject(**nwbfile_kwargs["Subject"])
                else:
                    nwb_file = NWBFile(**nwbfile_kwargs)
                io.write(nwb_file)
    else:
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

        imaging_plane = add_scan_to_nwb(session_key, nwbfile=nwb_file)
        add_image_series_to_nwb(session_key, imaging_plane=imaging_plane)
        add_segmentation_data_to_nwb(session_key, nwbfile=nwb_file, imaging_plane=imaging_plane)

        return nwb_file


## TODO: Add a `from_source` flag as with ephys NWB with options for 