import datajoint as dj
import scanreader
import numpy as np
import pathlib
from datetime import datetime
from uuid import UUID
import os

from .imaging import schema, Scan, ScanInfo, Channel, PhysicalFile
from .utils import dict_to_hash

from djutils.templates import required, optional

from img_loaders import suite2p_loader, caiman_loader

# ===================================== Lookup =====================================


@schema
class ProcessingMethod(dj.Lookup):
    definition = """
    processing_method: char(8)
    """

    contents = zip(['suite2p', 'caiman'])


@schema
class ProcessingParamSet(dj.Lookup):
    definition = """
    paramset_idx:  smallint
    ---
    -> ProcessingMethod    
    paramset_desc: varchar(128)
    param_set_hash: uuid
    unique index (param_set_hash)
    params: longblob  # dictionary of all applicable parameters
    """

    @classmethod
    def insert_new_params(cls, processing_method: str, paramset_idx: int, paramset_desc: str, params: dict):
        param_dict = {'processing_method': processing_method,
                      'paramset_idx': paramset_idx,
                      'paramset_desc': paramset_desc,
                      'params': params,
                      'param_set_hash': UUID(dict_to_hash(params))}
        q_param = cls & {'param_set_hash': param_dict['param_set_hash']}

        if q_param:  # If the specified param-set already exists
            pname = q_param.fetch1('param_set_name')
            if pname == paramset_idx:  # If the existed set has the same name: job done
                return
            else:  # If not same name: human error, trying to add the same paramset with different name
                raise dj.DataJointError('The specified param-set already exists - name: {}'.format(pname))
        else:
            cls.insert1(param_dict)


@schema
class CellCompartment(dj.Lookup):
    definition = """  # cell compartments that can be imaged
    cell_compartment         : char(16)
    """

    contents = zip(['axon', 'soma', 'bouton'])


@schema
class MaskType(dj.Lookup):
    definition = """ # possible classifications for a segmented mask
    mask_type        : varchar(16)
    """

    contents = zip(['soma', 'axon', 'dendrite', 'neuropil', 'artefact', 'unknown'])


# ===================================== Trigger a processing routine =====================================

@schema
class ProcessingTask(dj.Manual):
    definition = """
    -> Scan
    -> ProcessingParamSet
    ---
    task_mode='load': enum('load', 'trigger')  # 'load': load computed analysis results, 'trigger': trigger computation
    """


@schema
class Processing(dj.Computed):
    definition = """
    -> ProcessingTask
    ---
    proc_completion_time     : datetime  # time of generation of this set of processed, segmented results
    proc_start_time=null     : datetime  # execution time of this processing task (not available if analysis triggering is NOT required)
    proc_curation_time=null  : datetime  # time of lastest curation (modification to the file) on this result set
    """

    class ProcessingOutputFile(dj.Part):
        definition = """
        -> master
        -> PhysicalFile
        """

    @staticmethod
    @optional
    def _get_caiman_dir(processing_task_key: dict) -> str:
        """
        Retrieve the CaImAn output directory for a given ProcessingTask
        :param processing_task_key: a dictionary of one ProcessingTask
        :return: a string for full path to the resulting CaImAn output directory
        """
        return None

    @staticmethod
    @optional
    def _get_suite2p_dir(processing_task_key: dict) -> str:
        """
        Retrieve the Suite2p output directory for a given ProcessingTask
        :param processing_task_key: a dictionary of one ProcessingTask
        :return: a string for full path to the resulting Suite2p output directory
        """
        return None

    # Run processing only on Scan with ScanInfo inserted
    @property
    def key_source(self):
        return ProcessingTask & ScanInfo

    def make(self, key):
        method, task_mode = (ProcessingParamSet * ProcessingTask & key).fetch1('processing_method', 'task_mode')

        if task_mode == 'load':
            if method == 'suite2p':
                if (ScanInfo & key).fetch1('nrois') > 0:
                    raise NotImplementedError(f'Suite2p ingestion error - Unable to handle ScanImage multi-ROI scanning mode yet')

                data_dir = pathlib.Path(Processing._get_suite2p_dir(key))
                loaded_s2p = suite2p_loader.Suite2p(data_dir)
                key = {**key, 'proc_completion_time': loaded_s2p.creation_time, 'proc_curation_time': loaded_s2p.curation_time}
                # Insert file(s)
                root = pathlib.Path(PhysicalFile._get_root_data_dir())
                output_files = data_dir.glob('*')
                output_files = [f.relative_to(root).as_posix() for f in output_files if f.is_file()]

            elif method == 'caiman':
                data_dir = pathlib.Path(Processing._get_caiman_dir(key))
                loaded_cm = caiman_loader.CaImAn(data_dir)

                key = {**key, 'proc_completion_time': loaded_cm.creation_time,
                              'proc_curation_time': loaded_cm.curation_time}

                # Insert file(s)
                root = pathlib.Path(PhysicalFile._get_root_data_dir())
                output_files = [loaded_cm.caiman_fp.relative_to(root).as_posix()]
            else:
                raise NotImplementedError('Unknown method: {}'.format(method))

            self.insert1(key)
            PhysicalFile.insert(zip(output_files), skip_duplicates=True)
            self.ProcessingOutputFile.insert([{**key, 'file_path': f} for f in output_files], ignore_extra_fields=True)

        elif task_mode == 'trigger':
            start_time = datetime.now()
            # trigger Suite2p or CaImAn here
            # wait for completion, then insert with "completion_time", "start_time", no "curation_time"
            return


# ===================================== Motion Correction =====================================

@schema
class MotionCorrection(dj.Imported):
    definition = """ 
    -> Processing
    ---
    -> Channel.proj(mc_channel='channel')              # channel used for motion correction in this processing task
    """

    class RigidMotionCorrection(dj.Part):
        definition = """ 
        -> master
        ---
        outlier_frames=null             : longblob      # mask with true for frames with outlier shifts (already corrected)
        y_shifts                        : longblob      # (pixels) y motion correction shifts
        x_shifts                        : longblob      # (pixels) x motion correction shifts
        z_shifts=null                   : longblob      # (pixels) z motion correction shifts (z-drift) 
        y_std                           : float         # (pixels) standard deviation of y shifts across all frames
        x_std                           : float         # (pixels) standard deviation of x shifts across all frames
        z_std=null                      : float         # (pixels) standard deviation of z shifts across all frames
        """

    class NonRigidMotionCorrection(dj.Part):
        """ Piece-wise rigid motion correction - tile the FOV into multiple 3D blocks/patches"""
        definition = """ 
        -> master
        ---
        outlier_frames=null             : longblob      # mask with true for frames with outlier shifts (already corrected)
        block_height                    : int           # (pixels)
        block_width                     : int           # (pixels)
        block_depth                     : int           # (pixels)
        block_count_y                   : int           # number of blocks tiled in the y direction
        block_count_x                   : int           # number of blocks tiled in the x direction
        block_count_z                   : int           # number of blocks tiled in the z direction
        """

    class Block(dj.Part):
        definition = """  # FOV-tiled blocks used for non-rigid motion correction
        -> master.NonRigidMotionCorrection
        block_id                        : int
        ---
        block_y                         : longblob      # (y_start, y_end) in pixel of this block
        block_x                         : longblob      # (x_start, x_end) in pixel of this block
        block_z                         : longblob      # (z_start, z_end) in pixel of this block
        y_shifts                        : longblob      # (pixels) y motion correction shifts for every frame
        x_shifts                        : longblob      # (pixels) x motion correction shifts for every frame
        z_shifts=null                   : longblob      # (pixels) x motion correction shifts for every frame
        y_std                           : float         # (pixels) standard deviation of y shifts across all frames
        x_std                           : float         # (pixels) standard deviation of x shifts across all frames
        z_std=null                      : float         # (pixels) standard deviation of z shifts across all frames
        """

    class Summary(dj.Part):
        definition = """ # summary images for each field and channel after corrections
        -> master
        -> ScanInfo.Field
        ---
        ref_image                    : longblob      # image used as alignment template
        average_image                : longblob      # mean of registered frames
        correlation_image=null       : longblob      # correlation map (computed during cell detection)
        max_proj_image=null          : longblob      # max of registered frames
        """

    def make(self, key):

        method = (ProcessingParamSet * ProcessingTask & key).fetch1('processing_method')

        if method == 'suite2p':
            data_dir = pathlib.Path(Processing._get_suite2p_dir(key))
            loaded_s2p = suite2p_loader.Suite2p(data_dir)

            field_keys = (ScanInfo.Field & key).fetch('KEY', order_by='field_z')

            align_chn = loaded_s2p.planes[0].alignment_channel

            # ---- iterate through all s2p plane outputs ----
            rigid_mc, nonrigid_mc, nonrigid_blocks = {}, {}, {}
            summary_imgs = []
            for idx, (plane, s2p) in enumerate(loaded_s2p.planes.items()):
                # -- rigid motion correction --
                if idx == 0:
                    rigid_mc = {**key,
                                'y_shifts': s2p.ops['yoff'],
                                'x_shifts': s2p.ops['xoff'],
                                'z_shifts': np.full_like(s2p.ops['xoff'], 0),
                                'y_std': np.nanstd(s2p.ops['yoff']),
                                'x_std': np.nanstd(s2p.ops['xoff']),
                                'z_std': np.nan,
                                'outlier_frames': s2p.ops['badframes']}
                else:
                    rigid_mc['y_shifts'] = np.vstack([rigid_mc['y_shifts'], s2p.ops['yoff']])
                    rigid_mc['y_std'] = np.nanstd(rigid_mc['y_shifts'].flatten())
                    rigid_mc['x_shifts'] = np.vstack([rigid_mc['x_shifts'], s2p.ops['xoff']])
                    rigid_mc['x_std'] = np.nanstd(rigid_mc['x_shifts'].flatten())
                    rigid_mc['outlier_frames'] = np.logical_or(rigid_mc['outlier_frames'], s2p.ops['badframes'])
                # -- non-rigid motion correction --
                if s2p.ops['nonrigid']:
                    if idx == 0:
                        nonrigid_mc = {**key,
                                       'block_height': s2p.ops['block_size'][0],
                                       'block_width': s2p.ops['block_size'][1],
                                       'block_depth': 1,
                                       'block_count_y': s2p.ops['nblocks'][0],
                                       'block_count_x': s2p.ops['nblocks'][1],
                                       'block_count_z': len(loaded_s2p.planes),
                                       'outlier_frames': s2p.ops['badframes']}
                    else:
                        nonrigid_mc['outlier_frames'] = np.logical_or(nonrigid_mc['outlier_frames'], s2p.ops['badframes'])
                    for b_id, (b_y, b_x, bshift_y, bshift_x) in enumerate(zip(s2p.ops['xblock'], s2p.ops['yblock'],
                                                                              s2p.ops['yoff1'].T, s2p.ops['xoff1'].T)):
                        if b_id in nonrigid_blocks:
                            nonrigid_blocks[b_id]['y_shifts'] = np.vstack([nonrigid_blocks[b_id]['y_shifts'], bshift_y])
                            nonrigid_blocks[b_id]['y_std'] = np.nanstd(nonrigid_blocks[b_id]['y_shifts'].flatten())
                            nonrigid_blocks[b_id]['x_shifts'] = np.vstack([nonrigid_blocks[b_id]['x_shifts'], bshift_x])
                            nonrigid_blocks[b_id]['x_std'] = np.nanstd(nonrigid_blocks[b_id]['x_shifts'].flatten())
                        else:
                            nonrigid_blocks[b_id] = {**key, 'block_id': b_id,
                                                     'block_y': b_y, 'block_x': b_x,
                                                     'block_z': np.full_like(b_x, plane),
                                                     'y_shifts': bshift_y, 'x_shifts': bshift_x,
                                                     'z_shifts': np.full((len(loaded_s2p.planes), len(bshift_x)), 0),
                                                     'y_std': np.nanstd(bshift_y), 'x_std': np.nanstd(bshift_x),
                                                     'z_std': np.nan}

                # -- summary images --
                mc_key = (ScanInfo.Field * ProcessingTask & key & field_keys[plane]).fetch1('KEY')
                summary_imgs.append({**mc_key,
                                     'ref_image': s2p.ref_image,
                                     'average_image': s2p.mean_image,
                                     'correlation_image': s2p.correlation_map,
                                     'max_proj_image': s2p.max_proj_image})

            self.insert1({**key, 'mc_channel': align_chn})
            self.RigidMotionCorrection.insert1(rigid_mc)
            self.NonRigidMotionCorrection.insert1(nonrigid_mc)
            self.Block.insert(nonrigid_blocks.values())
            self.Summary.insert(summary_imgs)

        elif method == 'caiman':
            data_dir = pathlib.Path(Processing._get_caiman_dir(key))
            loaded_cm = caiman_loader.CaImAn(data_dir)

            self.insert1({**key, 'mc_channel': loaded_cm.alignment_channel})
            
            is3D = loaded_cm.params.motion['is3D']
            # -- rigid motion correction --
            if not loaded_cm.params.motion['pw_rigid']:
                rigid_mc = {**key,
                            'x_shifts': loaded_cm.motion_correction['shifts_rig'][:, 0],
                            'y_shifts': loaded_cm.motion_correction['shifts_rig'][:, 1],
                            'z_shifts': (loaded_cm.motion_correction['shifts_rig'][:, 2]
                                         if is3D
                                         else np.full_like(loaded_cm.motion_correction['shifts_rig'][:, 0], 0)),
                            'x_std': np.nanstd(loaded_cm.motion_correction['shifts_rig'][:, 0]),
                            'y_std': np.nanstd(loaded_cm.motion_correction['shifts_rig'][:, 1]),
                            'z_std': (np.nanstd(loaded_cm.motion_correction['shifts_rig'][:, 2])
                                      if is3D
                                      else np.nan),
                            'outlier_frames': None}

                self.RigidMotionCorrection.insert1(rigid_mc)

            # -- non-rigid motion correction --
            else:
                nonrigid_mc = {
                    **key,
                    'block_height': loaded_cm.params.motion['strides'][0] + loaded_cm.params.motion['overlaps'][0],
                    'block_width': loaded_cm.params.motion['strides'][1] + loaded_cm.params.motion['overlaps'][1],
                    'block_depth': (loaded_cm.params.motion['strides'][2] + loaded_cm.params.motion['overlaps'][2]
                                    if is3D else 1),
                    'block_count_x': len(set(loaded_cm.motion_correction['coord_shifts_els'][:, 0])),
                    'block_count_y': len(set(loaded_cm.motion_correction['coord_shifts_els'][:, 2])),
                    'block_count_z': (len(set(loaded_cm.motion_correction['coord_shifts_els'][:, 4]))
                                      if is3D else 1),
                    'outlier_frames': None}

                nonrigid_blocks = []
                for b_id in range(len(loaded_cm.motion_correction['x_shifts_els'][0, :])):
                    nonrigid_blocks.append(
                        {**key, 'block_id': b_id,
                         'block_x': np.arange(*loaded_cm.motion_correction['coord_shifts_els'][b_id, 0:2]),
                         'block_y': np.arange(*loaded_cm.motion_correction['coord_shifts_els'][b_id, 2:4]),
                         'block_z': (np.arange(*loaded_cm.motion_correction['coord_shifts_els'][b_id, 4:6])
                                     if is3D
                                     else np.full_like(np.arange(*loaded_cm.motion_correction['coord_shifts_els'][b_id, 0:2], 0))),
                         'x_shifts': loaded_cm.motion_correction['x_shifts_els'][:, b_id],
                         'y_shifts': loaded_cm.motion_correction['y_shifts_els'][:, b_id],
                         'z_shifts': (loaded_cm.motion_correction['z_shifts_els'][:, b_id]
                                      if is3D
                                      else np.full_like(loaded_cm.motion_correction['x_shifts_els'][:, b_id], 0)),
                         'x_std': np.nanstd(loaded_cm.motion_correction['x_shifts_els'][:, b_id]),
                         'y_std': np.nanstd(loaded_cm.motion_correction['y_shifts_els'][:, b_id]),
                         'z_std': (np.nanstd(loaded_cm.motion_correction['z_shifts_els'][:, b_id])
                                   if is3D
                                   else np.nan)})

                self.NonRigidMotionCorrection.insert1(nonrigid_mc)
                self.Block.insert(nonrigid_blocks)

            # -- summary images --
            field_keys = (ScanInfo.Field & key).fetch('KEY', order_by='field_z')

            summary_imgs = [{**fkey, 'ref_image': ref_image,
                             'average_image': ave_img,
                             'correlation_image': corr_img,
                             'max_proj_image': max_img}
                            for fkey, ref_image, ave_img, corr_img, max_img in zip(
                    field_keys,
                    loaded_cm.motion_correction['reference_image'].transpose(2, 0, 1) if is3D else loaded_cm.motion_correction['reference_image'][np.newaxis, ...],
                    loaded_cm.motion_correction['average_image'].transpose(2, 0, 1) if is3D else loaded_cm.motion_correction['average_image'][np.newaxis, ...],
                    loaded_cm.motion_correction['correlation_image'].transpose(2, 0, 1) if is3D else loaded_cm.motion_correction['correlation_image'][np.newaxis, ...],
                    loaded_cm.motion_correction['max_image'].transpose(2, 0, 1) if is3D else loaded_cm.motion_correction['max_image'][np.newaxis, ...])]

            self.Summary.insert(summary_imgs)

        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))

# ===================================== Segmentation =====================================


@schema
class Segmentation(dj.Computed):
    definition = """ # Different mask segmentations.
    -> MotionCorrection    
    """

    class Mask(dj.Part):
        definition = """ # A mask produced by segmentation.
        -> master
        mask                : smallint
        ---
        -> Channel.proj(seg_channel='channel')   # channel used for the segmentation
        mask_npix                : int           # number of pixels in ROIs
        mask_center_x            : int           # center x coordinate in pixel
        mask_center_y            : int           # center y coordinate in pixel
        mask_center_z            : int           # center z coordinate in pixel
        mask_xpix                : longblob      # x coordinates in pixels
        mask_ypix                : longblob      # y coordinates in pixels      
        mask_zpix                : longblob      # z coordinates in pixels        
        mask_weights             : longblob      # weights of the mask at the indices above in column major (Fortran) order
        """

    def make(self, key):
        method = (ProcessingParamSet * ProcessingTask & key).fetch1('processing_method')

        if method == 'suite2p':
            data_dir = pathlib.Path(Processing._get_suite2p_dir(key))
            loaded_s2p = suite2p_loader.Suite2p(data_dir)
            field_keys = (ScanInfo.Field & key).fetch('KEY', order_by='field_z')

            # ---- iterate through all s2p plane outputs ----
            masks, cells = [], []
            for plane, s2p in loaded_s2p.planes.items():
                mask_count = len(masks)  # increment mask id from all "plane"
                for mask_idx, (is_cell, cell_prob, mask_stat) in enumerate(zip(s2p.iscell, s2p.cell_prob, s2p.stat)):
                    masks.append({**key, 'mask': mask_idx + mask_count, 'seg_channel': s2p.segmentation_channel,
                                  'mask_npix': mask_stat['npix'],
                                  'mask_center_x':  mask_stat['med'][1],
                                  'mask_center_y':  mask_stat['med'][0],
                                  'mask_center_z': mask_stat.get('iplane', plane),
                                  'mask_xpix':  mask_stat['xpix'],
                                  'mask_ypix':  mask_stat['ypix'],
                                  'mask_zpix': np.full(mask_stat['npix'], mask_stat.get('iplane', plane)),
                                  'mask_weights':  mask_stat['lam']})
                    if is_cell:
                        cells.append({**key, 'mask_classification_method': 'suite2p_default_classifier',
                                      'mask': mask_idx + mask_count, 'mask_type': 'soma', 'confidence': cell_prob})

            self.insert1(key)
            self.Mask.insert(masks, ignore_extra_fields=True)

            if cells:
                MaskClassification.insert1({**key, 'mask_classification_method': 'suite2p_default_classifier'}, allow_direct_insert=True)
                MaskClassification.MaskType.insert(cells, ignore_extra_fields=True, allow_direct_insert=True)
        
        elif method == 'caiman':
            data_dir = pathlib.Path(Processing._get_caiman_dir(key))
            loaded_cm = caiman_loader.CaImAn(data_dir)

            # infer "segmentation_channel" - from params if available, else from caiman loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
            seg_channel = params.get('segmentation_channel', loaded_cm.segmentation_channel)

            masks, cells = [], []
            for mask in loaded_cm.masks:
                masks.append({**key, 'seg_channel': seg_channel,
                              'mask': mask['mask_id'],
                              'mask_npix': mask['mask_npix'],
                              'mask_center_x': mask['mask_center_x'],
                              'mask_center_y': mask['mask_center_y'],
                              'mask_center_z': mask['mask_center_z'],
                              'mask_xpix': mask['mask_xpix'],
                              'mask_ypix': mask['mask_ypix'],
                              'mask_zpix': mask['mask_zpix'],
                              'mask_weights': mask['mask_weights']})
                if mask['mask_id'] in loaded_cm.cnmf.estimates.idx_components:
                    cells.append({**key, 'mask_classification_method': 'caiman_default',
                                  'mask': mask['mask_id'], 'mask_type': 'soma'})

            self.insert1(key)
            self.Mask.insert(masks, ignore_extra_fields=True)

            if cells:
                MaskClassification.insert1({**key, 'mask_classification_method': 'caiman_default'}, allow_direct_insert=True)
                MaskClassification.MaskType.insert(cells, ignore_extra_fields=True, allow_direct_insert=True)

        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))


@schema
class MaskClassificationMethod(dj.Lookup):
    definition = """
    mask_classification_method: varchar(32)
    """

    contents = zip(['suite2p_default_classifier'])


@schema
class MaskClassification(dj.Computed):
    definition = """
    -> Segmentation
    -> MaskClassificationMethod
    """

    class MaskType(dj.Part):
        definition = """
        -> master
        -> Segmentation.Mask
        ---
        -> MaskType
        confidence=null: float
        """

    def make(self, key):
        pass


# ===================================== Activity Trace =====================================


@schema
class Fluorescence(dj.Computed):
    definition = """  # fluorescence traces before spike extraction or filtering
    -> Segmentation
    """

    class Trace(dj.Part):
        definition = """
        -> master
        -> Segmentation.Mask
        -> Channel.proj(fluo_channel='channel')  # the channel that this trace comes from         
        ---
        fluorescence                : longblob  # fluorescence trace associated with this mask
        neuropil_fluorescence=null  : longblob  # Neuropil fluorescence trace
        """

    def make(self, key):
        method = (ProcessingParamSet * ProcessingTask & key).fetch1('processing_method')

        if method == 'suite2p':
            data_dir = pathlib.Path(Processing._get_suite2p_dir(key))
            loaded_s2p = suite2p_loader.Suite2p(data_dir)

            # ---- iterate through all s2p plane outputs ----
            fluo_traces, fluo_chn2_traces = [], []
            for s2p in loaded_s2p.planes.values():
                mask_count = len(fluo_traces)  # increment mask id from all "plane"
                for mask_idx, (f, fneu) in enumerate(zip(s2p.F, s2p.Fneu)):
                    fluo_traces.append({**key, 'mask': mask_idx + mask_count,
                                        'fluo_channel': 0,
                                        'fluorescence': f, 'neuropil_fluorescence': fneu})
                if len(s2p.F_chan2):
                    mask_chn2_count = len(fluo_chn2_traces)  # increment mask id from all "plane"
                    for mask_idx, (f2, fneu2) in enumerate(zip(s2p.F_chan2, s2p.Fneu_chan2)):
                        fluo_chn2_traces.append({**key, 'mask': mask_idx + mask_chn2_count,
                                                 'fluo_channel': 1,
                                                 'fluorescence': f2, 'neuropil_fluorescence': fneu2})

            self.insert1(key)
            self.Trace.insert(fluo_traces + fluo_chn2_traces)

        elif method == 'caiman':
            data_dir = pathlib.Path(Processing._get_caiman_dir(key))
            loaded_cm = caiman_loader.CaImAn(data_dir)

            # infer "segmentation_channel" - from params if available, else from caiman loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
            seg_channel = params.get('segmentation_channel', loaded_cm.segmentation_channel)

            fluo_traces = []
            for mask in loaded_cm.masks:
                fluo_traces.append({**key, 'mask': mask['mask_id'], 'fluo_channel': seg_channel,
                                    'fluorescence': mask['inferred_trace']})

            self.insert1(key)
            self.Trace.insert(fluo_traces)
        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))


@schema
class ActivityExtractionMethod(dj.Lookup):
    definition = """
    extraction_method: varchar(32)
    """

    contents = zip(['suite2p_deconvolution', 'caiman_deconvolution', 'caiman_dff'])


@schema
class Activity(dj.Computed):
    definition = """  # inferred neural activity from fluorescence trace - e.g. dff, spikes
    -> Fluorescence
    -> ActivityExtractionMethod
    """

    class Trace(dj.Part):
        definition = """  #
        -> master
        -> Fluorescence.Trace
        ---
        activity_trace: longblob  # 
        """

    def make(self, key):

        method = (ProcessingParamSet * ProcessingTask & key).fetch1('processing_method')

        if method == 'suite2p':
            if key['extraction_method'] == 'suite2p_deconvolution':
                data_dir = pathlib.Path(Processing._get_suite2p_dir(key))
                loaded_s2p = suite2p_loader.Suite2p(data_dir)

                self.insert1(key)

                # ---- iterate through all s2p plane outputs ----
                spikes = []
                for s2p in loaded_s2p.planes.values():
                    mask_count = len(spikes)  # increment mask id from all "plane"
                    for mask_idx, spks in enumerate(s2p.spks):
                        spikes.append({**key, 'mask': mask_idx + mask_count,
                                       'fluo_channel': 0,
                                       'activity_trace': spks})
                self.Trace.insert(spikes)
                
        elif method == 'caiman':
            if key['extraction_method'] in ('caiman_deconvolution', 'caiman_dff'):
                attr_mapper = {'caiman_deconvolution': 'spikes', 'caiman_dff': 'dff'}

                data_dir = pathlib.Path(Processing._get_caiman_dir(key))
                loaded_cm = caiman_loader.CaImAn(data_dir)

                # infer "segmentation_channel" - from params if available, else from caiman loader
                params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
                seg_channel = params.get('segmentation_channel', loaded_cm.segmentation_channel)

                activities = []
                for mask in loaded_cm.masks:
                    activities.append({**key, 'mask': mask['mask_id'],
                                       'fluo_channel': seg_channel,
                                       'activity_trace': mask[attr_mapper[key['extraction_method']]]})
                self.insert1(key)
                self.Trace.insert(activities)

        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))
