from datetime import datetime
from uuid import uuid4

import datajoint as dj
import matplotlib.pyplot as plt
import numpy as np
from dateutil.tz import tzlocal

from pynwb import NWBHDF5IO, NWBFile, TimeSeries
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


def add_scan_to_nwb(session_key, nwbfile, nwbfile_kwargs=None):
    from math import nan

    scan_keys = (scan.Scan & session_key).fetch("KEY")

    for scan_key in scan_keys:
        scan_data = (scan.Scan & scan_key).fetch1("scanner", "scan_notes")
        device = nwbfile.create_device(
            name=scan_data["scanner"]
            if scan_data["scanner"] is not None
            else "TwoPhotonMicroscope",
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
                    description=scan_data["scan_notes"]
                    if session_info["scan_notes"] != ""
                    else f"Imaging plane for channel {channel+1}",
                    device=device,
                    excitation_lambda=nan,
                    indicator="unknown",
                    location="unknown",
                    grid_spacing=(0.01, 0.01),
                    grid_spacing_unit="meters",
                    origin_coords=[1.0, 2.0, 3.0],
                    origin_coords_units="meters",
                )


def add_data_to_nwb(session_key, nwbfile, raw_data):
    if raw_data:
        imaging_data = get_image_files(session_key)
        frame_rate = (scan.ScanInfo & session_key).fetch1("fps")
        two_p_series = TwoPhotonSeries(
            name="TwoPhotonSeries",
            data=imaging_data,
            imaging_plane=imaging_plane,
            rate=frame_rate,
            unit="raw fluorescence",
        )
    else:
        imaging_files = (scan.ScanInfo.ScanFile & session_key).fetch("file_path")


def add_motion_correction_to_nwb(session_key, nwbfile):
    pass


def imaging_session_to_nwb(
    session_key,
    raw=True,
    spikes=True,
    lfp="source",
    end_frame=None,
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

    add_scan_to_nwb(session_key, nwbfile, **nwbfile_kwargs)
    add_data_to_nwb(session_key, nwbfile, raw_data=raw)

    try:
        (imaging.MotionCorrection & "scan_id='1'").fetch1("KEY")
        add_motion_correction_to_nwb(session_key)
    except DataJointError:
        raise DataJointError(f"No motion correction data found for key {session_key}")

    return nwbfile
