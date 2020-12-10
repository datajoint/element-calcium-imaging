import datajoint as dj
import scanreader
import numpy as np
import pathlib

from djutils.templates import required

from .file import schema, PhysicalFile

# ===================================== Lookup =====================================


@schema
class Channel(dj.Lookup):
    definition = """  # A recording channel
    channel     : tinyint  # 0-based indexing
    """
    contents = zip(range(5))


# ===================================== ScanImage's scan =====================================


@schema
class Scan(dj.Manual):

    _Session = ...      # reference to Session
    _Equipment = ...    # reference to Equipment

    definition = """    
    -> self._Session    
    scan_id: int        
    ---
    -> self._Equipment  
    scan_notes='' : varchar(4095)         # free-notes
    """


@schema
class ScanLocation(dj.Manual):

    _Location = ...   # reference to a Location table

    definition = """
    -> Scan       
    -> self._Location      
    """


@schema
class ScanInfo(dj.Imported):
    definition = """ # general data about the reso/meso scans, from ScanImage header
    -> Scan
    ---
    nfields                 : tinyint           # number of fields
    nchannels               : tinyint           # number of channels
    ndepths                 : int               # Number of scanning depths (planes)
    nframes                 : int               # number of recorded frames
    nrois                   : tinyint           # number of ROIs (see scanimage's multi ROI imaging)
    x                       : float             # (um) ScanImage's 0 point in the motor coordinate system
    y                       : float             # (um) ScanImage's 0 point in the motor coordinate system
    fps                     : float             # (Hz) frames per second
    bidirectional           : boolean           # true = bidirectional scanning
    usecs_per_line          : float             # microseconds per scan line
    fill_fraction           : float             # raster scan temporal fill fraction (see scanimage)
    """

    class Field(dj.Part):
        definition = """ # field-specific scan information
        -> master
        field_idx           : int
        ---
        px_height           : smallint      # height in pixels
        px_width            : smallint      # width in pixels
        um_height=null      : float         # height in microns
        um_width=null       : float         # width in microns
        field_x             : float         # (um) center of field in the motor coordinate system
        field_y             : float         # (um) center of field in the motor coordinate system
        field_z             : float         # (um) relative depth of field
        delay_image         : longblob      # (ms) delay between the start of the scan and pixels in this field
        """

    class ScanFile(dj.Part):
        definition = """
        -> master
        -> PhysicalFile
        """

    @staticmethod
    @required
    def _get_scan_image_files(scan_key: dict) -> list:
        """
        Get the list of ScanImage files associated with a given Scan
        :param scan_key: key of a Scan
        :return: list of ScanImage files' full file-paths
        """
        return None

    def make(self, key):
        """ Read and store some scan meta information."""
        # Read the scan
        print('Reading header...')
        scan_filenames = ScanInfo._get_scan_image_files(key)
        scan = scanreader.read_scan(scan_filenames)

        # Insert in ScanInfo
        self.insert1(dict(key,
                          nfields=scan.num_fields,
                          nchannels=scan.num_channels,
                          nframes=scan.num_frames,
                          ndepths=scan.num_scanning_depths,
                          x=scan.motor_position_at_zero[0],
                          y=scan.motor_position_at_zero[1],
                          fps=scan.fps,
                          bidirectional=scan.is_bidirectional,
                          usecs_per_line=scan.seconds_per_line * 1e6,
                          fill_fraction=scan.temporal_fill_fraction,
                          nrois=scan.num_rois if scan.is_multiROI else 0))

        # Insert Field(s)
        x_zero, y_zero, z_zero = scan.motor_position_at_zero  # motor x, y, z at ScanImage's 0
        if scan.is_multiROI:
            self.Field.insert([dict(key,
                                    field_idx=field_id,
                                    px_height=scan.field_heights[field_id],
                                    px_width=scan.field_widths[field_id],
                                    um_height=scan.field_heights_in_microns[field_id],
                                    um_width=scan.field_widths_in_microns[field_id],
                                    field_x=x_zero + scan._degrees_to_microns(scan.fields[field_id].x),
                                    field_y=y_zero + scan._degrees_to_microns(scan.fields[field_id].y),
                                    field_z=z_zero + scan.fields[field_id].depth,
                                    delay_image=scan.field_offsets[field_id])
                               for field_id in range(scan.num_fields)])
        else:
            self.Field.insert([dict(key,
                                    field_idx=plane_idx,
                                    px_height=scan.image_height,
                                    px_width=scan.image_width,
                                    um_height=getattr(scan, 'image_height_in_microns', None),
                                    um_width=getattr(scan, 'image_width_in_microns', None),
                                    field_x=x_zero,
                                    field_y=y_zero,
                                    field_z=z_zero + scan.scanning_depths[plane_idx],
                                    delay_image=scan.field_offsets[plane_idx])
                               for plane_idx in range(scan.num_scanning_depths)])

        # Insert file(s)
        root = pathlib.Path(PhysicalFile._get_root_data_dir())
        scan_files = [pathlib.Path(f).relative_to(root).as_posix() for f in scan_filenames]
        PhysicalFile.insert(zip(scan_files), skip_duplicates=True)
        self.ScanFile.insert([{**key, 'file_path': f} for f in scan_files])
