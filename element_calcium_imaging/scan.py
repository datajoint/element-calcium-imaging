import datajoint as dj
import pathlib
import importlib
import inspect
from element_interface.utils import find_root_directory, find_full_path

schema = dj.schema()

_linking_module = None


def activate(
    scan_schema_name, *, create_schema=True, create_tables=True, linking_module=None
):
    """
    activate(scan_schema_name, *, create_schema=True, create_tables=True, linking_module=None)
        :param scan_schema_name: schema name on the database server to activate the `scan` module
        :param create_schema: when True (default), create schema in the database if it does not yet exist.
        :param create_tables: when True (default), create tables in the database if they do not yet exist.
        :param linking_module: a module name or a module containing the
         required dependencies to activate the `scan` module:
            Upstream tables:
                + Session: parent table to Scan, typically identifying a recording session
                + Equipment: Reference table for Scan, specifying the equipment used for the acquisition of this scan
                + Location: Reference table for ScanLocation, specifying the brain location where this scan is acquired
            Functions:
                + get_imaging_root_data_dir() -> list
                    Retrieve the full path for the root data directory - e.g. containing the imaging recording files or analysis results for all subject/sessions.
                    :return: a string (or list of string) for full path to the root data directory
                + get_scan_image_files(scan_key: dict) -> list
                    Retrieve the list of ScanImage files associated with a given Scan
                    :param scan_key: key of a Scan
                    :return: list of ScanImage files' full file-paths
                + get_scan_box_files(scan_key: dict) -> list
                    Retrieve the list of Scanbox files (*.sbx) associated with a given Scan
                    :param scan_key: key of a Scan
                    :return: list of Scanbox files' full file-paths
                + get_processed_root_data_dir() -> str:
                    Retrieves the root directory for all processed data to be found from or written to
                    :return: a string for full path to the root directory for processed data
    """

    if isinstance(linking_module, str):
        linking_module = importlib.import_module(linking_module)
    assert inspect.ismodule(
        linking_module
    ), "The argument 'dependency' must be a module's name or a module"

    global _linking_module
    _linking_module = linking_module

    schema.activate(
        scan_schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        add_objects=_linking_module.__dict__,
    )


# Functions required by element-calcium-imaging  -------------------------------


def get_imaging_root_data_dir() -> str:
    """
    All data paths, directories in DataJoint Elements are recommended to be stored as
    relative paths (posix format), with respect to some user-configured "root" directory,
     which varies from machine to machine (e.g. different mounted drive locations)

    get_imaging_root_data_dir() -> list
        This user-provided function retrieves the possible root data directories
         containing the imaging data for all subjects/sessions
         (e.g. acquired ScanImage raw files,
         output files from processing routines, etc.)
        :return: a string for full path to the imaging root data directory,
         or list of strings for possible root data directories
    """

    root_directories = _linking_module.get_imaging_root_data_dir()
    if isinstance(root_directories, (str, pathlib.Path)):
        root_directories = [root_directories]

    if hasattr(_linking_module, "get_processed_root_data_dir"):
        root_directories.append(_linking_module.get_processed_root_data_dir())

    return root_directories


def get_processed_root_data_dir() -> str:
    """
    get_processed_root_data_dir() -> str:
        Retrieves the root directory for all processed data to be found from or written to
        :return: a string for full path to the root directory for processed data
    """

    if hasattr(_linking_module, "get_processed_root_data_dir"):
        return _linking_module.get_processed_root_data_dir()
    else:
        return get_imaging_root_data_dir()[0]


def get_scan_image_files(scan_key: dict) -> list:
    """
    Retrieve the list of ScanImage files associated with a given Scan
    :param scan_key: key of a Scan
    :return: list of ScanImage files' full file-paths
    """
    return _linking_module.get_scan_image_files(scan_key)


def get_scan_box_files(scan_key: dict) -> list:
    """
    Retrieve the list of Scanbox files (*.sbx) associated with a given Scan
    :param scan_key: key of a Scan
    :return: list of Scanbox files' full file-paths
    """
    return _linking_module.get_scan_box_files(scan_key)


def get_nd2_files(scan_key: dict) -> list:
    """
    Retrieve the list of Nikon files (*.nd2) associated with a given Scan
    :param scan_key: key of a Scan
    :return: list of Nikon files' full file-paths
    """
    return _linking_module.get_nd2_files(scan_key)


def get_prairieview_files(scan_key: dict) -> list:
    """
    Retrieve the list of Bruker PrairieView tif files (*.tif) with a given Scan
    :param scan_key: key of a Scan
    :return: list of Bruker PrairieView files' full file-paths
    """
    return _linking_module.get_prairieview_files(scan_key)


# ----------------------------- Table declarations ----------------------


@schema
class AcquisitionSoftware(dj.Lookup):
    definition = """  # Name of acquisition software - e.g. ScanImage, Scanbox, NIS, PrairieView
    acq_software: varchar(24)    
    """
    contents = zip(["ScanImage", "Scanbox", "NIS", "PrairieView"])


@schema
class Channel(dj.Lookup):
    definition = """  # A recording channel
    channel     : tinyint  # 0-based indexing
    """
    contents = zip(range(5))


@schema
class Scan(dj.Manual):
    definition = """    
    -> Session
    scan_id: int        
    ---
    -> [nullable] Equipment  
    -> AcquisitionSoftware  
    scan_notes='' : varchar(4095)         # free-notes
    """


@schema
class ScanLocation(dj.Manual):
    definition = """
    -> Scan   
    ---    
    -> Location      
    """


@schema
class ScanInfo(dj.Imported):
    definition = """ # general data about the reso/meso scans from header
    -> Scan
    ---
    nfields              : tinyint   # number of fields
    nchannels            : tinyint   # number of channels
    ndepths              : int       # Number of scanning depths (planes)
    nframes              : int       # number of recorded frames
    nrois                : tinyint   # number of ROIs (see scanimage's multi ROI imaging)
    x=null               : float     # (um) ScanImage's 0 point in the motor coordinate system
    y=null               : float     # (um) ScanImage's 0 point in the motor coordinate system
    z=null               : float     # (um) ScanImage's 0 point in the motor coordinate system
    fps                  : float     # (Hz) frames per second - Volumetric Scan Rate 
    bidirectional        : boolean   # true = bidirectional scanning
    usecs_per_line=null  : float     # microseconds per scan line
    fill_fraction=null   : float     # raster scan temporal fill fraction (see scanimage)
    scan_datetime=null   : datetime  # datetime of the scan
    scan_duration=null   : float     # (seconds) duration of the scan
    bidirectional_z=null : boolean   # true = bidirectional z-scan
    """

    class Field(dj.Part):
        definition = """ # field-specific scan information
        -> master
        field_idx         : int
        ---
        px_height         : smallint  # height in pixels
        px_width          : smallint  # width in pixels
        um_height=null    : float     # height in microns
        um_width=null     : float     # width in microns
        field_x=null      : float     # (um) center of field in the motor coordinate system
        field_y=null      : float     # (um) center of field in the motor coordinate system
        field_z=null      : float     # (um) relative depth of field
        delay_image=null  : longblob  # (ms) delay between the start of the scan and pixels in this field
        roi=null          : int       # the scanning roi (as recorded in the acquisition software) containing this field - only relevant to mesoscale scans
        """

    class ScanFile(dj.Part):
        definition = """
        -> master
        file_path: varchar(255)  # filepath relative to root data directory
        """

    def make(self, key):
        acq_software = (Scan & key).fetch1("acq_software")

        if acq_software == "ScanImage":
            import scanreader

            # Read the scan
            scan_filepaths = get_scan_image_files(key)
            scan = scanreader.read_scan(scan_filepaths)

            # Insert in ScanInfo
            x_zero = (
                scan.motor_position_at_zero[0] if scan.motor_position_at_zero else None
            )
            y_zero = (
                scan.motor_position_at_zero[1] if scan.motor_position_at_zero else None
            )
            z_zero = (
                scan.motor_position_at_zero[2] if scan.motor_position_at_zero else None
            )

            self.insert1(
                dict(
                    key,
                    nfields=scan.num_fields,
                    nchannels=scan.num_channels,
                    nframes=scan.num_frames,
                    ndepths=scan.num_scanning_depths,
                    x=x_zero,
                    y=y_zero,
                    z=z_zero,
                    fps=scan.fps,
                    bidirectional=scan.is_bidirectional,
                    usecs_per_line=scan.seconds_per_line * 1e6,
                    fill_fraction=scan.temporal_fill_fraction,
                    nrois=scan.num_rois if scan.is_multiROI else 0,
                    scan_duration=scan.num_frames / scan.fps,
                )
            )
            # Insert Field(s)
            if scan.is_multiROI:
                self.Field.insert(
                    [
                        dict(
                            key,
                            field_idx=field_id,
                            px_height=scan.field_heights[field_id],
                            px_width=scan.field_widths[field_id],
                            um_height=scan.field_heights_in_microns[field_id],
                            um_width=scan.field_widths_in_microns[field_id],
                            field_x=x_zero
                            + scan._degrees_to_microns(scan.fields[field_id].x)
                            if x_zero
                            else None,
                            field_y=y_zero
                            + scan._degrees_to_microns(scan.fields[field_id].y)
                            if y_zero
                            else None,
                            field_z=z_zero + scan.fields[field_id].depth
                            if z_zero
                            else None,
                            delay_image=scan.field_offsets[field_id],
                            roi=scan.field_rois[field_id][0],
                        )
                        for field_id in range(scan.num_fields)
                    ]
                )
            else:
                self.Field.insert(
                    [
                        dict(
                            key,
                            field_idx=plane_idx,
                            px_height=scan.image_height,
                            px_width=scan.image_width,
                            um_height=getattr(
                                scan, "image_height_in_microns", None),
                            um_width=getattr(
                                scan, "image_width_in_microns", None),
                            field_x=x_zero if x_zero else None,
                            field_y=y_zero if y_zero else None,
                            field_z=z_zero + scan.scanning_depths[plane_idx]
                            if z_zero
                            else None,
                            delay_image=scan.field_offsets[plane_idx],
                        )
                        for plane_idx in range(scan.num_scanning_depths)
                    ]
                )
        elif acq_software == "Scanbox":
            import sbxreader

            # Read the scan
            scan_filepaths = get_scan_box_files(key)
            sbx_meta = sbxreader.sbx_get_metadata(scan_filepaths[0])
            sbx_matinfo = sbxreader.sbx_get_info(scan_filepaths[0])
            is_multiROI = bool(
                sbx_matinfo.mesoscope.enabled
            )  # currently not handling "multiROI" ingestion

            if is_multiROI:
                raise NotImplementedError(
                    "Loading routine not implemented for Scanbox multiROI scan mode"
                )

            # Insert in ScanInfo
            x_zero, y_zero, z_zero = sbx_meta["stage_pos"]
            self.insert1(
                dict(
                    key,
                    nfields=sbx_meta["num_fields"]
                    if is_multiROI
                    else sbx_meta["num_planes"],
                    nchannels=sbx_meta["num_channels"],
                    nframes=sbx_meta["num_frames"],
                    ndepths=sbx_meta["num_planes"],
                    x=x_zero,
                    y=y_zero,
                    z=z_zero,
                    fps=sbx_meta["frame_rate"],
                    bidirectional=sbx_meta == "bidirectional",
                    nrois=sbx_meta["num_rois"] if is_multiROI else 0,
                    scan_duration=(
                        sbx_meta["num_frames"] / sbx_meta["frame_rate"]),
                )
            )
            # Insert Field(s)
            if not is_multiROI:
                px_width, px_height = sbx_meta["frame_size"]
                self.Field.insert(
                    [
                        dict(
                            key,
                            field_idx=plane_idx,
                            px_height=px_height,
                            px_width=px_width,
                            um_height=px_height * sbx_meta["um_per_pixel_y"]
                            if sbx_meta["um_per_pixel_y"]
                            else None,
                            um_width=px_width * sbx_meta["um_per_pixel_x"]
                            if sbx_meta["um_per_pixel_x"]
                            else None,
                            field_x=x_zero,
                            field_y=y_zero,
                            field_z=z_zero + sbx_meta["etl_pos"][plane_idx],
                        )
                        for plane_idx in range(sbx_meta["num_planes"])
                    ]
                )
        elif acq_software == "NIS":
            import nd2

            # Read the scan
            scan_filepaths = get_nd2_files(key)
            nd2_file = nd2.ND2File(scan_filepaths[0])
            is_multiROI = False  # MultiROI to be implemented later

            # Frame per second
            try:
                fps = 1000 / \
                    nd2_file.experiment[0].parameters.periods[0].periodDiff.avg
            except:
                fps = 1000 / nd2_file.experiment[0].parameters.periodDiff.avg

            # Estimate ND2 file scan duration
            def estimate_nd2_scan_duration(nd2_scan_obj):
                # Calculates scan duration for Nikon images
                ti = (
                    nd2_scan_obj.frame_metadata(0)
                    .channels[0]
                    .time.absoluteJulianDayNumber
                )  # Initial frame's JD.
                tf = (
                    nd2_scan_obj.frame_metadata(nd2_scan_obj.shape[0] - 1)
                    .channels[0]
                    .time.absoluteJulianDayNumber
                )  # Final frame's JD.

                return (tf - ti) * 86400 + 1 / fps

            scan_duration = sum(
                estimate_nd2_scan_duration(nd2.ND2File(f)) for f in scan_filepaths
            )

            # Insert in ScanInfo
            self.insert1(
                dict(
                    key,
                    nfields=nd2_file.sizes.get("P", 1),
                    nchannels=nd2_file.attributes.channelCount,
                    nframes=nd2_file.metadata.contents.frameCount,
                    ndepths=nd2_file.sizes.get("Z", 1),
                    x=None,
                    y=None,
                    z=None,
                    fps=fps,
                    bidirectional=bool(
                        nd2_file.custom_data["GrabberCameraSettingsV1_0"][
                            "GrabberCameraSettings"
                        ]["PropertiesQuality"]["ScanDirection"]
                    ),
                    nrois=0,
                    scan_duration=scan_duration,
                )
            )

            # MultiROI to be implemented later

            # Insert in Field
            if not is_multiROI:
                self.Field.insert(
                    [
                        dict(
                            key,
                            field_idx=plane_idx,
                            px_height=nd2_file.attributes.heightPx,
                            px_width=nd2_file.attributes.widthPx,
                            um_height=nd2_file.attributes.heightPx
                            * nd2_file.voxel_size().y,
                            um_width=nd2_file.attributes.widthPx
                            * nd2_file.voxel_size().x,
                            field_x=None,
                            field_y=None,
                            field_z=None,
                        )
                        for plane_idx in range(nd2_file.sizes.get("Z", 1))
                    ]
                )
        elif acq_software == "PrairieView":
            from element_interface import prairieviewreader

            scan_filepaths = get_prairieview_files(key)
            pvscan_info = prairieviewreader.get_pv_metadata(
                scan_filepaths[0])
            self.insert1(
                dict(
                    key,
                    nfields=pvscan_info["num_fields"],
                    nchannels=pvscan_info["num_channels"],
                    ndepths=pvscan_info["num_planes"],
                    nframes=pvscan_info["num_frames"],
                    nrois=pvscan_info["num_rois"],
                    x=pvscan_info["x_pos"],
                    y=pvscan_info["y_pos"],
                    z=pvscan_info["z_pos"],
                    fps=pvscan_info["frame_rate"],
                    bidirectional=pvscan_info["bidirectional"],
                    bidirectional_z=pvscan_info["bidirectional_z"],
                    usecs_per_line=pvscan_info["usecs_per_line"],
                    scan_datetime=pvscan_info["scan_datetime"],
                    scan_duration=pvscan_info["scan_duration"],
                )
            )

            self.Field.insert(
                dict(
                    key,
                    field_idx=plane_idx,
                    px_height=pvscan_info["height_in_pixels"],
                    px_width=pvscan_info["width_in_pixels"],
                    um_height=pvscan_info["height_in_um"],
                    um_width=pvscan_info["width_in_um"],
                    field_x=pvscan_info["fieldX"],
                    field_y=pvscan_info["fieldY"],
                    field_z=pvscan_info["fieldZ"][plane_idx],
                )
                for plane_idx in range(pvscan_info["num_planes"])
            )
        else:
            raise NotImplementedError(
                f"Loading routine not implemented for {acq_software} "
                "acquisition software"
            )

        # Insert file(s)
        root_dir = find_root_directory(
            get_imaging_root_data_dir(), scan_filepaths[0])

        scan_files = [
            pathlib.Path(f).relative_to(root_dir).as_posix() for f in scan_filepaths
        ]
        self.ScanFile.insert([{**key, "file_path": f} for f in scan_files])
