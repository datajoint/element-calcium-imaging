import datajoint as dj
import numpy as np
import pathlib
from datetime import datetime
import uuid
import hashlib
import importlib
import inspect

from . import scan

schema = dj.schema()

_linking_module = None


def activate(imaging_schema_name, scan_schema_name=None, *,
             create_schema=True, create_tables=True, linking_module=None):
    """
    activate(imaging_schema_name, *, scan_schema_name=None, create_schema=True, create_tables=True, linking_module=None)
        :param imaging_schema_name: schema name on the database server to activate the `imaging` module
        :param scan_schema_name: schema name on the database server to activate the `scan` module
         - may be omitted if the `scan` module is already activated
        :param create_schema: when True (default), create schema in the database if it does not yet exist.
        :param create_tables: when True (default), create tables in the database if they do not yet exist.
        :param linking_module: a module name or a module containing the
         required dependencies to activate the `imaging` module:
            Upstream tables:
                + Session: parent table to Scan, typically identifying a recording session
            Functions:
                + get_imaging_root_data_dir() -> str
                    Retrieve the root data directory - e.g. containing all subject/sessions data
                    :return: a string for full path to the root data directory
    """

    if isinstance(linking_module, str):
        linking_module = importlib.import_module(linking_module)
    assert inspect.ismodule(linking_module),\
        "The argument 'dependency' must be a module's name or a module"

    global _linking_module
    _linking_module = linking_module

    scan.activate(scan_schema_name, create_schema=create_schema,	
                  create_tables=create_tables, linking_module=linking_module)
    schema.activate(imaging_schema_name, create_schema=create_schema,
                    create_tables=create_tables, add_objects=_linking_module.__dict__)


# -------------- Functions required by the element-calcium-imaging  --------------

def get_imaging_root_data_dir() -> str:
    """
    get_imaging_root_data_dir() -> str
        Retrieve the root data directory - e.g. containing all subject/sessions data
        :return: a string for full path to the root data directory
    """
    return _linking_module.get_imaging_root_data_dir()


# -------------- Table declarations --------------


@schema
class ProcessingMethod(dj.Lookup):
    definition = """
    processing_method: char(24)
    ---
    processing_method_desc: varchar(1000)
    """

    contents = [('suite2p', 'suite2p analysis suite'),
                ('caiman', 'caiman analysis suite'),
                ('miniscope_analysis', 'miniscope analysis suite')]


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
    package_version=null: varchar(16)
    """

    @classmethod
    def insert_new_params(cls, processing_method: str, paramset_idx: int,
                          paramset_desc: str, params: dict):
        param_dict = {'processing_method': processing_method,
                      'package_version': package_version,
                      'paramset_idx': paramset_idx,
                      'paramset_desc': paramset_desc,
                      'params': params,
                      'param_set_hash': dict_to_uuid(params)}
        q_param = cls & {'param_set_hash': param_dict['param_set_hash']}

        if q_param:  # If the specified param-set already exists
            pname = q_param.fetch1('paramset_idx')
            if pname == paramset_idx:  # If the existed set has the same name: job done
                return
            else:  # If not same name: human error, trying to add the same paramset with different name
                raise dj.DataJointError(
                    'The specified param-set already exists - name: {}'.format(pname))
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


# -------------- Trigger a processing routine --------------

@schema
class ProcessingTask(dj.Manual):
    definition = """
    -> scan.Scan
    -> ProcessingParamSet
    ---
    processing_output_dir: varchar(255)         #  output directory of the processed scan relative to root data directory
    task_mode='load': enum('load', 'trigger')   # 'load': load computed analysis results, 'trigger': trigger computation
    """


@schema
class Processing(dj.Computed):
    definition = """
    -> ProcessingTask
    ---
    processing_time     : datetime  # time of generation of this set of processed, segmented results
    """

    # Run processing only on Scan with ScanInfo inserted
    @property
    def key_source(self):
        return ProcessingTask & scan.ScanInfo

    def make(self, key):
        task_mode = (ProcessingTask & key).fetch1('task_mode')
        method, loaded_result = get_loader_result(key, ProcessingTask)

        if task_mode == 'load':
            if method == 'suite2p':
                if (scan.ScanInfo & key).fetch1('nrois') > 0:
                    raise NotImplementedError(f'Suite2p ingestion error - Unable to handle'
                                              f' ScanImage multi-ROI scanning mode yet')
                loaded_suite2p = loaded_result
                key = {**key, 'processing_time': loaded_suite2p.creation_time}
            elif method == 'caiman':
                loaded_caiman = loaded_result
                key = {**key, 'processing_time': loaded_caiman.creation_time}
            else:
                raise NotImplementedError('Unknown method: {}'.format(method))
        elif task_mode == 'trigger':
            raise NotImplementedError(f'Automatic triggering of {method} analysis'
                                      f' is not yet supported')
        else:
            raise ValueError(f'Unknown task mode: {task_mode}')

        self.insert1(key)


@schema
class Curation(dj.Manual):
    definition = """
    -> Processing
    curation_id: int
    ---
    curation_time: datetime             # time of generation of this set of curated results 
    curation_output_dir: varchar(255)   # output directory of the curated results, relative to root data directory
    manual_curation: bool               # has manual curation been performed on this result?
    curation_note='': varchar(2000)  
    """

    def create1_from_processing_task(self, key, is_curated=False, curation_note=''):
        """
        A convenient function to create a new corresponding "Curation" for a particular "ProcessingTask"
        """
        if key not in Processing():
            raise ValueError(f'No corresponding entry in Processing available for: {key};'
                             f' do `Processing.populate(key)`')

        output_dir = (ProcessingTask & key).fetch1('processing_output_dir')
        method, loaded_result = get_loader_result(key, ProcessingTask)

        if method == 'suite2p':
            loaded_suite2p = loaded_result
            curation_time = loaded_suite2p.creation_time
        elif method == 'caiman':
            loaded_caiman = loaded_result
            curation_time = loaded_caiman.creation_time
        else:
            raise NotImplementedError('Unknown method: {}'.format(method))

        # Synthesize curation_id
        curation_id = dj.U().aggr(self & key, n='ifnull(max(curation_id)+1,1)').fetch1('n')
        self.insert1({**key, 'curation_id': curation_id,
                      'curation_time': curation_time, 'curation_output_dir': output_dir,
                      'manual_curation': is_curated,
                      'curation_note': curation_note})


# -------------- Motion Correction --------------

@schema
class MotionCorrection(dj.Imported):
    definition = """ 
    -> Processing
    ---
    -> scan.Channel.proj(motion_correct_channel='channel') # channel used for motion correction in this processing task
    """

    class RigidMotionCorrection(dj.Part):
        definition = """ 
        -> master
        ---
        outlier_frames=null : longblob  # mask with true for frames with outlier shifts (already corrected)
        y_shifts            : longblob  # (pixels) y motion correction shifts
        x_shifts            : longblob  # (pixels) x motion correction shifts
        z_shifts=null       : longblob  # (pixels) z motion correction shifts (z-drift) 
        y_std               : float     # (pixels) standard deviation of y shifts across all frames
        x_std               : float     # (pixels) standard deviation of x shifts across all frames
        z_std=null          : float     # (pixels) standard deviation of z shifts across all frames
        """

    class NonRigidMotionCorrection(dj.Part):
        """
        Piece-wise rigid motion correction
        - tile the FOV into multiple 3D blocks/patches
        """
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
        block_id        : int
        ---
        block_y         : longblob  # (y_start, y_end) in pixel of this block
        block_x         : longblob  # (x_start, x_end) in pixel of this block
        block_z         : longblob  # (z_start, z_end) in pixel of this block
        y_shifts        : longblob  # (pixels) y motion correction shifts for every frame
        x_shifts        : longblob  # (pixels) x motion correction shifts for every frame
        z_shifts=null   : longblob  # (pixels) x motion correction shifts for every frame
        y_std           : float     # (pixels) standard deviation of y shifts across all frames
        x_std           : float     # (pixels) standard deviation of x shifts across all frames
        z_std=null      : float     # (pixels) standard deviation of z shifts across all frames
        """

    class Summary(dj.Part):
        definition = """ # summary images for each field and channel after corrections
        -> master
        -> scan.ScanInfo.Field
        ---
        ref_image               : longblob  # image used as alignment template
        average_image           : longblob  # mean of registered frames
        correlation_image=null  : longblob  # correlation map (computed during cell detection)
        max_proj_image=null     : longblob  # max of registered frames
        """

    def make(self, key):
        method, loaded_result = get_loader_result(key, ProcessingTask)

        if method == 'suite2p':
            loaded_suite2p = loaded_result

            field_keys = (scan.ScanInfo.Field & key).fetch('KEY', order_by='field_z')

            motion_correct_channel = loaded_suite2p.planes[0].alignment_channel

            # ---- iterate through all s2p plane outputs ----
            rigid_correction, nonrigid_correction, nonrigid_blocks = {}, {}, {}
            summary_images = []
            for idx, (plane, s2p) in enumerate(loaded_suite2p.planes.items()):
                # -- rigid motion correction --
                if idx == 0:
                    rigid_correction = {
                        **key,
                        'y_shifts': s2p.ops['yoff'],
                        'x_shifts': s2p.ops['xoff'],
                        'z_shifts': np.full_like(s2p.ops['xoff'], 0),
                        'y_std': np.nanstd(s2p.ops['yoff']),
                        'x_std': np.nanstd(s2p.ops['xoff']),
                        'z_std': np.nan,
                        'outlier_frames': s2p.ops['badframes']}
                else:
                    rigid_correction['y_shifts'] = np.vstack(
                        [rigid_correction['y_shifts'], s2p.ops['yoff']])
                    rigid_correction['y_std'] = np.nanstd(
                        rigid_correction['y_shifts'].flatten())
                    rigid_correction['x_shifts'] = np.vstack(
                        [rigid_correction['x_shifts'], s2p.ops['xoff']])
                    rigid_correction['x_std'] = np.nanstd(
                        rigid_correction['x_shifts'].flatten())
                    rigid_correction['outlier_frames'] = np.logical_or(
                        rigid_correction['outlier_frames'], s2p.ops['badframes'])
                # -- non-rigid motion correction --
                if s2p.ops['nonrigid']:
                    if idx == 0:
                        nonrigid_correction = {
                            **key,
                            'block_height': s2p.ops['block_size'][0],
                            'block_width': s2p.ops['block_size'][1],
                            'block_depth': 1,
                            'block_count_y': s2p.ops['nblocks'][0],
                            'block_count_x': s2p.ops['nblocks'][1],
                            'block_count_z': len(loaded_suite2p.planes),
                            'outlier_frames': s2p.ops['badframes']}
                    else:
                        nonrigid_correction['outlier_frames'] = np.logical_or(
                            nonrigid_correction['outlier_frames'], s2p.ops['badframes'])
                    for b_id, (b_y, b_x, bshift_y, bshift_x) in enumerate(
                            zip(s2p.ops['xblock'], s2p.ops['yblock'],
                                s2p.ops['yoff1'].T, s2p.ops['xoff1'].T)):
                        if b_id in nonrigid_blocks:
                            nonrigid_blocks[b_id]['y_shifts'] = np.vstack(
                                [nonrigid_blocks[b_id]['y_shifts'], bshift_y])
                            nonrigid_blocks[b_id]['y_std'] = np.nanstd(
                                nonrigid_blocks[b_id]['y_shifts'].flatten())
                            nonrigid_blocks[b_id]['x_shifts'] = np.vstack(
                                [nonrigid_blocks[b_id]['x_shifts'], bshift_x])
                            nonrigid_blocks[b_id]['x_std'] = np.nanstd(
                                nonrigid_blocks[b_id]['x_shifts'].flatten())
                        else:
                            nonrigid_blocks[b_id] = {
                                **key, 'block_id': b_id,
                                'block_y': b_y, 'block_x': b_x,
                                'block_z': np.full_like(b_x, plane),
                                'y_shifts': bshift_y, 'x_shifts': bshift_x,
                                'z_shifts': np.full((len(loaded_suite2p.planes),
                                                     len(bshift_x)), 0),
                                'y_std': np.nanstd(bshift_y), 'x_std': np.nanstd(bshift_x),
                                'z_std': np.nan}

                # -- summary images --
                motion_correction_key = (scan.ScanInfo.Field * ProcessingTask
                                         & key & field_keys[plane]).fetch1('KEY')
                summary_images.append({**motion_correction_key,
                                       'ref_image': s2p.ref_image,
                                       'average_image': s2p.mean_image,
                                       'correlation_image': s2p.correlation_map,
                                       'max_proj_image': s2p.max_proj_image})

            self.insert1({**key, 'motion_correct_channel': motion_correct_channel})
            if rigid_correction:
                self.RigidMotionCorrection.insert1(rigid_correction)
            if nonrigid_correction:
                self.NonRigidMotionCorrection.insert1(nonrigid_correction)
                self.Block.insert(nonrigid_blocks.values())
            self.Summary.insert(summary_images)

        elif method == 'caiman':
            loaded_caiman = loaded_result

            self.insert1({**key, 'motion_correct_channel': loaded_caiman.alignment_channel})

            is3D = loaded_caiman.params.motion['is3D']
            # -- rigid motion correction --
            if not loaded_caiman.params.motion['pw_rigid']:
                rigid_correction = {
                    **key,
                    'x_shifts': loaded_caiman.motion_correction['shifts_rig'][:, 0],
                    'y_shifts': loaded_caiman.motion_correction['shifts_rig'][:, 1],
                    'z_shifts': (loaded_caiman.motion_correction['shifts_rig'][:, 2]
                                 if is3D
                                 else np.full_like(
                        loaded_caiman.motion_correction['shifts_rig'][:, 0], 0)),
                    'x_std': np.nanstd(loaded_caiman.motion_correction['shifts_rig'][:, 0]),
                    'y_std': np.nanstd(loaded_caiman.motion_correction['shifts_rig'][:, 1]),
                    'z_std': (np.nanstd(loaded_caiman.motion_correction['shifts_rig'][:, 2])
                              if is3D
                              else np.nan),
                    'outlier_frames': None}

                self.RigidMotionCorrection.insert1(rigid_correction)

            # -- non-rigid motion correction --
            else:
                nonrigid_correction = {
                    **key,
                    'block_height': (loaded_caiman.params.motion['strides'][0]
                                     + loaded_caiman.params.motion['overlaps'][0]),
                    'block_width': (loaded_caiman.params.motion['strides'][1]
                                    + loaded_caiman.params.motion['overlaps'][1]),
                    'block_depth': (loaded_caiman.params.motion['strides'][2]
                                    + loaded_caiman.params.motion['overlaps'][2]
                                    if is3D else 1),
                    'block_count_x': len(
                        set(loaded_caiman.motion_correction['coord_shifts_els'][:, 0])),
                    'block_count_y': len(
                        set(loaded_caiman.motion_correction['coord_shifts_els'][:, 2])),
                    'block_count_z': (len(
                        set(loaded_caiman.motion_correction['coord_shifts_els'][:, 4]))
                                      if is3D else 1),
                    'outlier_frames': None}

                nonrigid_blocks = []
                for b_id in range(len(loaded_caiman.motion_correction['x_shifts_els'][0, :])):
                    nonrigid_blocks.append(
                        {**key, 'block_id': b_id,
                         'block_x': np.arange(*loaded_caiman.motion_correction[
                                                   'coord_shifts_els'][b_id, 0:2]),
                         'block_y': np.arange(*loaded_caiman.motion_correction[
                                                   'coord_shifts_els'][b_id, 2:4]),
                         'block_z': (np.arange(*loaded_caiman.motion_correction[
                                                    'coord_shifts_els'][b_id, 4:6])
                                     if is3D
                                     else np.full_like(
                             np.arange(*loaded_caiman.motion_correction[
                                            'coord_shifts_els'][b_id, 0:2]), 0)),
                         'x_shifts': loaded_caiman.motion_correction[
                                         'x_shifts_els'][:, b_id],
                         'y_shifts': loaded_caiman.motion_correction[
                                         'y_shifts_els'][:, b_id],
                         'z_shifts': (loaded_caiman.motion_correction[
                                          'z_shifts_els'][:, b_id]
                                      if is3D
                                      else np.full_like(
                             loaded_caiman.motion_correction['x_shifts_els'][:, b_id], 0)),
                         'x_std': np.nanstd(loaded_caiman.motion_correction[
                                                'x_shifts_els'][:, b_id]),
                         'y_std': np.nanstd(loaded_caiman.motion_correction[
                                                'y_shifts_els'][:, b_id]),
                         'z_std': (np.nanstd(loaded_caiman.motion_correction[
                                                 'z_shifts_els'][:, b_id])
                                   if is3D
                                   else np.nan)})

                self.NonRigidMotionCorrection.insert1(nonrigid_correction)
                self.Block.insert(nonrigid_blocks)

            # -- summary images --
            field_keys = (scan.ScanInfo.Field & key).fetch('KEY', order_by='field_z')
            summary_images = [
                {**key, **fkey, 'ref_image': ref_image,
                 'average_image': ave_img,
                 'correlation_image': corr_img,
                 'max_proj_image': max_img}
                for fkey, ref_image, ave_img, corr_img, max_img in zip(
                    field_keys,
                    loaded_caiman.motion_correction['reference_image'].transpose(2, 0, 1)
                    if is3D else loaded_caiman.motion_correction[
                        'reference_image'][...][np.newaxis, ...],
                    loaded_caiman.motion_correction['average_image'].transpose(2, 0, 1)
                    if is3D else loaded_caiman.motion_correction[
                        'average_image'][...][np.newaxis, ...],
                    loaded_caiman.motion_correction['correlation_image'].transpose(2, 0, 1)
                    if is3D else loaded_caiman.motion_correction[
                        'correlation_image'][...][np.newaxis, ...],
                    loaded_caiman.motion_correction['max_image'].transpose(2, 0, 1)
                    if is3D else loaded_caiman.motion_correction[
                        'max_image'][...][np.newaxis, ...])]
            self.Summary.insert(summary_images)

        elif method == 'miniscope_analysis':
            from .readers import miniscope_analysis_loader

            data_dir = pathlib.Path(get_miniscope_analysis_dir(key))
            loaded_miniscope_analysis = miniscope_analysis_loader.MiniscopeAnalysis(data_dir)

            # TODO: add motion correction and block data

            # -- summary images --
            mc_key = (scan.ScanInfo.Field * ProcessingTask & key).fetch1('KEY')
            summary_imgs.append({**mc_key,
                                 'average_image': loaded_miniscope_analysis.average_image,
                                 'correlation_image': loaded_miniscope_analysis.correlation_image})

            self.insert1({**key, 'mc_channel': loaded_miniscope_analysis.alignment_channel})
            self.Summary.insert(summary_imgs)

        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))

# -------------- Segmentation --------------


@schema
class Segmentation(dj.Computed):
    definition = """ # Different mask segmentations.
    -> Curation
    ---
    -> MotionCorrection    
    """

    @property
    def key_source(self):
        return Curation & MotionCorrection

    class Mask(dj.Part):
        definition = """ # A mask produced by segmentation.
        -> master
        mask            : smallint
        ---
        -> scan.Channel.proj(segmentation_channel='channel')  # channel used for segmentation
        mask_npix       : int       # number of pixels in ROIs
        mask_center_x   : int       # center x coordinate in pixel
        mask_center_y   : int       # center y coordinate in pixel
        mask_center_z   : int       # center z coordinate in pixel
        mask_xpix       : longblob  # x coordinates in pixels
        mask_ypix       : longblob  # y coordinates in pixels      
        mask_zpix       : longblob  # z coordinates in pixels        
        mask_weights    : longblob  # weights of the mask at the indices above
        """



    def make(self, key):
        motion_correction_key = (MotionCorrection & key).fetch1('KEY')

        method, loaded_result = get_loader_result(key, Curation)

        if method == 'suite2p':
            loaded_suite2p = loaded_result

            # ---- iterate through all s2p plane outputs ----
            masks, cells = [], []
            for plane, s2p in loaded_suite2p.planes.items():
                mask_count = len(masks)  # increment mask id from all "plane"
                for mask_idx, (is_cell, cell_prob, mask_stat) in enumerate(zip(
                        s2p.iscell, s2p.cell_prob, s2p.stat)):
                    masks.append({
                        **key, 'mask': mask_idx + mask_count,
                        'segmentation_channel': s2p.segmentation_channel,
                        'mask_npix': mask_stat['npix'],
                        'mask_center_x':  mask_stat['med'][1],
                        'mask_center_y':  mask_stat['med'][0],
                        'mask_center_z': mask_stat.get('iplane', plane),
                        'mask_xpix':  mask_stat['xpix'],
                        'mask_ypix':  mask_stat['ypix'],
                        'mask_zpix': np.full(mask_stat['npix'],
                                             mask_stat.get('iplane', plane)),
                        'mask_weights':  mask_stat['lam']})
                    if is_cell:
                        cells.append({
                            **key,
                            'mask_classification_method': 'suite2p_default_classifier',
                            'mask': mask_idx + mask_count,
                            'mask_type': 'soma', 'confidence': cell_prob})

            self.insert1({**key, **motion_correction_key})
            self.Mask.insert(masks, ignore_extra_fields=True)

            if cells:
                MaskClassification.insert1({
                    **key,
                    'mask_classification_method': 'suite2p_default_classifier'},
                    allow_direct_insert=True)
                MaskClassification.MaskType.insert(cells,
                                                   ignore_extra_fields=True,
                                                   allow_direct_insert=True)
        
        elif method == 'caiman':
            loaded_caiman = loaded_result

            # infer "segmentation_channel" - from params if available, else from caiman loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
            segmentation_channel = params.get('segmentation_channel',
                                              loaded_caiman.segmentation_channel)

            masks, cells = [], []
            for mask in loaded_caiman.masks:
                masks.append({**key,
                              'segmentation_channel': segmentation_channel,
                              'mask': mask['mask_id'],
                              'mask_npix': mask['mask_npix'],
                              'mask_center_x': mask['mask_center_x'],
                              'mask_center_y': mask['mask_center_y'],
                              'mask_center_z': mask['mask_center_z'],
                              'mask_xpix': mask['mask_xpix'],
                              'mask_ypix': mask['mask_ypix'],
                              'mask_zpix': mask['mask_zpix'],
                              'mask_weights': mask['mask_weights']})
                if loaded_caiman.cnmf.estimates.idx_components is not None:
                    if mask['mask_id'] in loaded_caiman.cnmf.estimates.idx_components:
                        cells.append({
                            **key,
                            'mask_classification_method': 'caiman_default_classifier',
                            'mask': mask['mask_id'], 'mask_type': 'soma'})

            self.insert1({**key, **motion_correction_key})
            self.Mask.insert(masks, ignore_extra_fields=True)

            if cells:
                MaskClassification.insert1({
                    **key,
                    'mask_classification_method': 'caiman_default_classifier'},
                    allow_direct_insert=True)
                MaskClassification.MaskType.insert(cells,
                                                   ignore_extra_fields=True,
                                                   allow_direct_insert=True)

        elif method == 'miniscope_analysis':
            from .readers import miniscope_analysis_loader

            data_dir = pathlib.Path(get_miniscope_analysis_dir(key))
            loaded_miniscope_analysis = miniscope_analysis_loader.MiniscopeAnalysis(data_dir)

            # infer "segmentation_channel" - from params if available, else from miniscope analysis loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
            seg_channel = params.get('segmentation_channel', loaded_miniscope_analysis.segmentation_channel)

            masks = []
            for mask in loaded_miniscope_analysis.masks:
                masks.append({**key, 
                              'seg_channel': seg_channel,
                              'mask': mask['mask_id'],
                              'mask_npix': mask['mask_npix'],
                              'mask_center_x': mask['mask_center_x'],
                              'mask_center_y': mask['mask_center_y'],
                              'mask_xpix': mask['mask_xpix'],
                              'mask_ypix': mask['mask_ypix'],
                              'mask_weights': mask['mask_weights']})

            self.insert1(key)
            self.Mask.insert(masks, ignore_extra_fields=True)            

        else:
            raise NotImplementedError(f'Unknown/unimplemented method: {method}')


@schema
class MaskClassificationMethod(dj.Lookup):
    definition = """
    mask_classification_method: varchar(48)
    """

    contents = zip(['suite2p_default_classifier',
                    'caiman_default_classifier',
                    'miniscope_analysis_default_classifier'])


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


# -------------- Activity Trace --------------


@schema
class Fluorescence(dj.Computed):
    definition = """  # fluorescence traces before spike extraction or filtering
    -> Segmentation
    """

    class Trace(dj.Part):
        definition = """
        -> master
        -> Segmentation.Mask
        -> scan.Channel.proj(fluo_channel='channel')  # the channel that this trace comes from         
        ---
        fluorescence                : longblob  # fluorescence trace associated with this mask
        neuropil_fluorescence=null  : longblob  # Neuropil fluorescence trace
        """

    def make(self, key):
        method, loaded_result = get_loader_result(key, Curation)

        if method == 'suite2p':
            loaded_suite2p = loaded_result

            # ---- iterate through all s2p plane outputs ----
            fluo_traces, fluo_chn2_traces = [], []
            for s2p in loaded_suite2p.planes.values():
                mask_count = len(fluo_traces)  # increment mask id from all "plane"
                for mask_idx, (f, fneu) in enumerate(zip(s2p.F, s2p.Fneu)):
                    fluo_traces.append({
                        **key, 'mask': mask_idx + mask_count,
                        'fluo_channel': 0,
                        'fluorescence': f,
                        'neuropil_fluorescence': fneu})
                if len(s2p.F_chan2):
                    mask_chn2_count = len(fluo_chn2_traces) # increment mask id from all planes
                    for mask_idx, (f2, fneu2) in enumerate(zip(s2p.F_chan2, s2p.Fneu_chan2)):
                        fluo_chn2_traces.append({
                            **key, 'mask': mask_idx + mask_chn2_count,
                            'fluo_channel': 1,
                            'fluorescence': f2,
                            'neuropil_fluorescence': fneu2})

            self.insert1(key)
            self.Trace.insert(fluo_traces + fluo_chn2_traces)

        elif method == 'caiman':
            loaded_caiman = loaded_result

            # infer "segmentation_channel" - from params if available, else from caiman loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
            segmentation_channel = params.get('segmentation_channel',
                                              loaded_caiman.segmentation_channel)

            fluo_traces = []
            for mask in loaded_caiman.masks:
                fluo_traces.append({**key, 'mask': mask['mask_id'],
                                    'fluo_channel': segmentation_channel,
                                    'fluorescence': mask['inferred_trace']})

            self.insert1(key)
            self.Trace.insert(fluo_traces)
        
        elif method == 'miniscope_analysis':
            from .readers import miniscope_analysis_loader

            data_dir = pathlib.Path(get_miniscope_analysis_dir(key))
            loaded_miniscope_analysis = miniscope_analysis_loader.MiniscopeAnalysis(data_dir)

            # infer "segmentation_channel" - from params if available, else from miniscope analysis loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
            seg_channel = params.get('segmentation_channel', loaded_miniscope_analysis.segmentation_channel)

            fluo_traces = []
            for mask in loaded_miniscope_analysis.masks:
                fluo_traces.append({**key, 
                                    'mask': mask['mask_id'], 
                                    'fluo_channel': seg_channel,
                                    'fluorescence': mask['raw_trace']})

            self.insert1(key)
            self.Trace.insert(fluo_traces)
        
        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))


@schema
class ActivityExtractionMethod(dj.Lookup):
    definition = """
    extraction_method: varchar(32)
    """

    contents = zip(['suite2p_deconvolution', 'caiman_deconvolution', 'caiman_dff', 'miniscope_analysis_deconvolution', 'miniscope_analysis_dff'])


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

    @property
    def key_source(self):
        suite2p_key_source = (Fluorescence * ActivityExtractionMethod
                              * ProcessingParamSet.proj('processing_method')
                              & 'processing_method = "suite2p"'
                              & 'extraction_method LIKE "suite2p%"')
        caiman_key_source = (Fluorescence * ActivityExtractionMethod
                             * ProcessingParamSet.proj('processing_method')
                             & 'processing_method = "caiman"'
                             & 'extraction_method LIKE "caiman%"')
        return suite2p_key_source.proj() + caiman_key_source.proj()

    def make(self, key):
        method, loaded_result = get_loader_result(key, Curation)

        if method == 'suite2p':
            if key['extraction_method'] == 'suite2p_deconvolution':
                loaded_suite2p = loaded_result
                # ---- iterate through all s2p plane outputs ----
                spikes = []
                for s2p in loaded_suite2p.planes.values():
                    mask_count = len(spikes)  # increment mask id from all "plane"
                    for mask_idx, spks in enumerate(s2p.spks):
                        spikes.append({**key, 'mask': mask_idx + mask_count,
                                       'fluo_channel': 0,
                                       'activity_trace': spks})

                self.insert1(key)
                self.Trace.insert(spikes)
                
        elif method == 'caiman':
            loaded_caiman = loaded_result

            if key['extraction_method'] in ('caiman_deconvolution', 'caiman_dff'):
                attr_mapper = {'caiman_deconvolution': 'spikes', 'caiman_dff': 'dff'}

                # infer "segmentation_channel" - from params if available, else from caiman loader
                params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
                segmentation_channel = params.get('segmentation_channel',
                                                  loaded_caiman.segmentation_channel)

                activities = []
                for mask in loaded_caiman.masks:
                    activities.append({
                        **key, 'mask': mask['mask_id'],
                        'fluo_channel': segmentation_channel,
                        'activity_trace': mask[attr_mapper[key['extraction_method']]]})
                self.insert1(key)
                self.Trace.insert(activities)

        elif method == 'miniscope_analysis':
            if key['extraction_method'] in ('miniscope_analysis_deconvolution', 'miniscope_analysis_dff'):
                attr_mapper = {'miniscope_analysis_deconvolution': 'spikes', 'miniscope_analysis_dff': 'dff'}

                from .readers import miniscope_analysis_loader

                data_dir = pathlib.Path(get_miniscope_analysis_dir(key))
                loaded_miniscope_analysis = miniscope_analysis_loader.MiniscopeAnalysis(data_dir)

                # infer "segmentation_channel" - from params if available, else from miniscope analysis loader
                params = (ProcessingParamSet * ProcessingTask & key).fetch1('params')
                seg_channel = params.get('segmentation_channel', loaded_miniscope_analysis.segmentation_channel)

                activities = []
                for mask in loaded_miniscope_analysis.masks:
                    activities.append({**key, 
                                       'mask': mask['mask_id'],
                                       'fluo_channel': seg_channel,
                                       'activity_trace': mask[attr_mapper[key['extraction_method']]]})
                self.insert1(key)
                self.Trace.insert(activities)

        else:
            raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))

# ---------------- HELPER FUNCTIONS ----------------


_table_attribute_mapper = {'ProcessingTask': 'processing_output_dir',
                           'Curation': 'curation_output_dir'}


def get_loader_result(key, table):
    """
    Retrieve the loaded processed imaging results from the loader (e.g. suite2p, caiman, etc.)
        :param key: the `key` to one entry of ProcessingTask or Curation
        :param table: the class defining the table to retrieve
         the loaded results from (e.g. ProcessingTask, Curation)
        :return: a loader object of the loaded results
         (e.g. suite2p.Suite2p, caiman.CaImAn, etc.)
    """
    method, output_dir = (ProcessingParamSet * table & key).fetch1(
        'processing_method', _table_attribute_mapper[table.__name__])

    root_dir = pathlib.Path(get_imaging_root_data_dir())
    output_dir = root_dir / output_dir

    if method == 'suite2p':
        from .readers import suite2p_loader
        loaded_output = suite2p_loader.Suite2p(output_dir)
    elif method == 'caiman':
        from .readers import caiman_loader
        loaded_output = caiman_loader.CaImAn(output_dir)
    else:
        raise NotImplementedError('Unknown/unimplemented method: {}'.format(method))

    return method, loaded_output


def dict_to_uuid(key):
    """
    Given a dictionary `key`, returns a hash string as UUID
    """
    hashed = hashlib.md5()
    for k, v in sorted(key.items()):
        hashed.update(str(k).encode())
        hashed.update(str(v).encode())
    return uuid.UUID(hex=hashed.hexdigest())
