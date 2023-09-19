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
from ... import imaging_no_curation, imaging, imaging_preprocess
from ...scan import get_calcium_imaging_files, get_imaging_root_data_dir

logger = dj.logger

if imaging_no_curation.schema.is_activated():
    imaging = imaging_no_curation
else:
    raise DataJointError(
        "This export function is designed for the `imaging_no_curation` module."
    )


def _create_full_nwbfile(session_key, output_directory, nwb_path):
    acquisition_software = (scan.Scan & session_key).fetch1("acq_software")
    if acquisition_software == "NIS":
        raise NotImplementedError(
            "Packaging raw data from Nikon NIS acquisition software (.nd2 file format) is not currently supported."
        )

    session_paramset_key = (imaging.ProcessingTask & session_key).fetch1("paramset_idx")
    processing_method = (
        imaging.ProcessingParamSet & f"paramset_idx='{session_paramset_key}'"
    ).fetch1("processing_method")

    frame_rate = (scan.ScanInfo & session_key).fetch1("fps")

    if acquisition_software == "ScanImage" and processing_method == "suite2p":
        from neuroconv.datainterfaces import (
            ScanImageImagingInterface,
            Suite2pSegmentationInterface,
        )

        processing_folder_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )
        scan_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        s2p_interface = Suite2pSegmentationInterface(
            folder_path=processing_folder_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, s2p_interface])

    elif acquisition_software == "ScanImage" and processing_method == "CaImAn":
        from neuroconv.datainterfaces import (
            CaimanSegmentationInterface,
            ScanImageImagingInterface,
        )

        caiman_hdf5 = list(processing_folder_location.rglob("caiman_analysis.hdf5"))
        scan_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        caiman_interface = CaimanSegmentationInterface(file_path=caiman_hdf5[0])
        converter = ConverterPipe(data_interfaces=[scan_interface, caiman_interface])

    elif acquisition_software == "ScanImage" and processing_method == "extract":
        from neuroconv.datainterfaces import (
            ExtractSegmentationInterface,
            ScanImageImagingInterface,
        )

        processing_file_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )
        scan_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
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
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        s2p_interface = Suite2pSegmentationInterface(
            folder_path=processing_folder_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, s2p_interface])

    elif acquisition_software == "Scanbox" and processing_method == "CaImAn":
        from neuroconv.datainterfaces import (
            CaimanSegmentationInterface,
            SbxImagingInterface,
        )

        caiman_hdf5 = list(processing_folder_location.rglob("caiman_analysis.hdf5"))
        scan_interface = SbxImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        caiman_interface = CaimanSegmentationInterface(file_path=caiman_hdf5[0])
        converter = ConverterPipe(data_interfaces=[scan_interface, caiman_interface])

    elif acquisition_software == "Scanbox" and processing_method == "extract":
        from neuroconv.datainterfaces import (
            ExtractSegmentationInterface,
            SbxImagingInterface,
        )

        processing_file_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )
        scan_interface = SbxImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        extract_interface = ExtractSegmentationInterface(
            file_path=processing_file_location
        )
        converter = ConverterPipe(data_interfaces=[scan_interface, extract_interface])

    elif acquisition_software == "PrairieView" and processing_method == "suite2p":
        n_planes = (scan.ScanInfo & session_key).fetch1("ndepths")
        if n_planes > 1:
            from neuroconv.converters import (
                BrukerTiffMultiPlaneConverter as BrukerTiffConverter,
            )
        else:
            from neuroconv.converters import (
                BrukerTiffSinglePlaneConverter as BrukerTiffConverter,
            )
        from neuroconv.datainterfaces import Suite2pSegmentationInterface

        processing_folder_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )
        bruker_interface = BrukerTiffConverter(
            file_path=raw_data_files_location[0],
            fallback_sampling_frequency=frame_rate,
        )
        s2p_interface = Suite2pSegmentationInterface(
            folder_path=processing_folder_location
        )
        converter = ConverterPipe(data_interfaces=[bruker_interface, s2p_interface])

    elif acquisition_software == "PrairieView" and processing_method == "caiman":
        n_planes = (scan.ScanInfo & session_key).fetch1("ndepths")
        if n_planes > 1:
            from neuroconv.converters import (
                BrukerTiffMultiPlaneConverter as BrukerTiffConverter,
            )
        else:
            from neuroconv.converters import (
                BrukerTiffSinglePlaneConverter as BrukerTiffConverter,
            )
        from neuroconv.datainterfaces import CaimanSegmentationInterface

        processing_folder_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )
        bruker_interface = BrukerTiffConverter(
            file_path=raw_data_files_location[0],
            fallback_sampling_frequency=frame_rate,
        )
        caiman_hdf5 = list(processing_folder_location.rglob("caiman_analysis.hdf5"))
        caiman_interface = CaimanSegmentationInterface(file_path=caiman_hdf5[0])
        converter = ConverterPipe(data_interfaces=[bruker_interface, caiman_interface])

    elif acquisition_software == "PrairieView" and processing_method == "extract":
        n_planes = (scan.ScanInfo & session_key).fetch1("ndepths")
        if n_planes > 1:
            from neuroconv.converters import (
                BrukerTiffMultiPlaneConverter as BrukerTiffConverter,
            )
        else:
            from neuroconv.converters import (
                BrukerTiffSinglePlaneConverter as BrukerTiffConverter,
            )
        from neuroconv.datainterfaces import ExtractSegmentationInterface

        processing_file_location = pathlib.Path(output_directory).as_posix()
        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )
        bruker_interface = BrukerTiffConverter(
            file_path=raw_data_files_location[0],
            fallback_sampling_frequency=frame_rate,
        )
        extract_interface = ExtractSegmentationInterface(
            file_path=processing_file_location
        )
        converter = ConverterPipe(data_interfaces=[bruker_interface, extract_interface])

    metadata = converter.get_metadata()
    metadata["NWBFile"].update(session_description="DataJoint Session")
    converter.run_conversion(
        nwbfile_path=(nwb_path / f'{session_key["subject"]}_nwbfile'), metadata=metadata
    )


def _create_raw_data_nwbfile(session_key, output_directory, nwb_path):
    acquisition_software = (scan.Scan & session_key).fetch1("acq_software")
    frame_rate = (scan.ScanInfo & session_key).fetch1("fps")
    if acquisition_software == "ScanImage":
        from neuroconv.datainterfaces import ScanImageImagingInterface

        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )

        imaging_interface = ScanImageImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        metadata = imaging_interface.get_metadata()
        imaging_interface.run_conversion(
            nwbfile_path=(nwb_path / f'{session_key["subject"]}_nwbfile'),
            metadata=metadata,
        )

    elif acquisition_software == "Scanbox":
        from neuroconv.datainterfaces import SbxImagingInterface

        raw_data_files_location = get_calcium_imaging_files(
            session_key, acquisition_software
        )

        imaging_interface = SbxImagingInterface(
            file_path=raw_data_files_location[0], fallback_sampling_frequency=frame_rate
        )
        metadata = imaging_interface.get_metadata()
        imaging_interface.run_conversion(
            nwbfile_path=(nwb_path / f'{session_key["subject"]}_nwbfile'),
            metadata=metadata,
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
            nwbfile_path=(nwb_path / f'{session_key["subject"]}_nwbfile'),
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


def imaging_session_to_nwb(
    session_key,
    save_path=None,
    include_raw_data=False,
    processed_data_source="database",
    lab_key=None,
    project_key=None,
    protocol_key=None,
    nwbfile_kwargs=None,
):
    session_to_nwb = getattr(imaging._linking_module, "session_to_nwb", False)
    if processed_data_source not in ["database", "filesystem"]:
        raise ValueError(
            "Invalid processed data source. Expected one of 'database', 'filesystem'"
        )

    if not save_path:
        output_relative_dir = (imaging.ProcessingTask & session_key).fetch1(
            "processing_output_dir"
        )
        save_path = find_full_path(get_imaging_root_data_dir(), output_relative_dir)

    if include_raw_data and processed_data_source == "filesystem":
        _create_full_nwbfile(
            session_key, output_directory=save_path, nwb_path=save_path
        )
        with NWBHDF5IO(
            (save_path / f'{session_key["subject"]}_nwbfile'), mode="r+"
        ) as io:
            nwb_file = io.read()
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
            io.write(nwb_file)
    elif include_raw_data and processed_data_source == "database":
        _create_raw_data_nwbfile(
            session_key, output_directory=save_path, nwb_path=save_path
        )
        with NWBHDF5IO(
            (save_path / f'{session_key["subject"]}_nwbfile'), mode="r+"
        ) as io:
            nwb_file = io.read()
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
            try:
                io.write(nwb_file)
            except ValueError:
                logger.warn(
                    "Group already exists in NWB file. Unable to update values."
                )
    elif not include_raw_data and processed_data_source == "database":
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
        imaging_plane = _add_scan_to_nwb(session_key, nwbfile=nwb_file)
        _add_image_series_to_nwb(session_key, imaging_plane=imaging_plane)
        _add_segmentation_data_to_nwb(
            session_key, nwbfile=nwb_file, imaging_plane=imaging_plane
        )

        with NWBHDF5IO(
            (save_path / f'{session_key["subject"]}_nwbfile'), mode="w"
        ) as io:
            io.write(nwb_file)

    elif not include_raw_data and processed_data_source == "filesystem":
        raise NotImplementedError(
            "Creating NWB files without raw data from the filesystem is not supported. Please set `include_raw_data=True` or `processed_data_source='filesystem'`."
        )
