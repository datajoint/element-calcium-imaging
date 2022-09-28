import datajoint as dj
import numpy as np
import pathlib
import os
import inspect
import importlib
from element_interface.utils import find_full_path, dict_to_uuid, find_root_directory

from . import scan
from .scan import (
    get_imaging_root_data_dir,
    get_processed_root_data_dir,
    get_scan_image_files,
    get_scan_box_files,
    get_nd2_files,
)

schema = dj.Schema()

_linking_module = None


def activate(
    imaging_schema_name,
    scan_schema_name=None,
    *,
    create_schema=True,
    create_tables=True,
    linking_module=None,
):
    """
    activate(imaging_schema_name, *, scan_schema_name=None, create_schema=True, create_tables=True, linking_module=None)
        :param imaging_schema_name: schema name on the database server to activate the `imaging` module
        :param scan_schema_name: schema name on the database server to activate the `scan` module
         - may be omitted if the `scan` module is already activated
        :param create_schema: when True (default), create schema in the database if it does not yet exist.
        :param create_tables: when True (default), create tables in the database if they do not yet exist.
        :param linking_module: a module name or a module containing the
         required dependencies to activate the `imaging` module:
         + all that are required by the `scan` module
    """

    if isinstance(linking_module, str):
        linking_module = importlib.import_module(linking_module)
    assert inspect.ismodule(
        linking_module
    ), "The argument 'dependency' must be a module's name or a module"

    global _linking_module
    _linking_module = linking_module

    scan.activate(
        scan_schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        linking_module=linking_module,
    )
    schema.activate(
        imaging_schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        add_objects=_linking_module.__dict__,
    )


# -------------- Table declarations --------------


@schema
class PreprocessMethod(dj.Lookup):
    definition = """  #  Method/package used for pre-processing
    preprocess_method: varchar(16)
    ---
    preprocess_method_desc: varchar(1000)
    """


@schema
class PreprocessParamSet(dj.Lookup):
    definition = """  #  Parameter set used for pre-processing of calcium imaging data
    paramset_idx:  smallint
    ---
    -> PreprocessMethod
    paramset_desc: varchar(128)
    param_set_hash: uuid
    unique index (param_set_hash)
    params: longblob  # dictionary of all applicable parameters
    """

    @classmethod
    def insert_new_params(
        cls, preprocess_method: str, paramset_idx: int, paramset_desc: str, params: dict
    ):
        param_dict = {
            "preprocess_method": preprocess_method,
            "paramset_idx": paramset_idx,
            "paramset_desc": paramset_desc,
            "params": params,
            "param_set_hash": dict_to_uuid(params),
        }
        q_param = cls & {"param_set_hash": param_dict["param_set_hash"]}

        if q_param:  # If the specified param-set already exists
            pname = q_param.fetch1("paramset_idx")
            if pname == paramset_idx:  # If the existed set has the same name: job done
                return
            else:  # If not same name: human error, trying to add the same paramset with different name
                raise dj.DataJointError(
                    "The specified param-set already exists - name: {}".format(pname)
                )
        else:
            cls.insert1(param_dict)


@schema
class PreprocessParamSteps(dj.Manual):
    definition = """
    # Ordered list of paramset_idx that are to be run
    # When pre-processing is not performed, do not create an entry in `Step` Part table
    preprocess_param_steps_id: smallint
    ---
    preprocess_param_steps_name: varchar(32)
    preprocess_param_steps_desc: varchar(128)
    """

    class Step(dj.Part):
        definition = """
        -> master
        step_number: smallint                  # Order of operations
        ---
        -> PreprocessParamSet
        """


@schema
class PreprocessTask(dj.Manual):
    definition = """
    # Manual table for defining a pre-processing task ready to be run
    -> scan.Scan
    -> PreprocessParamSteps
    ---
    preprocess_output_dir: varchar(255)  # Pre-processing output directory relative 
                                         # to the root data directory
    task_mode='none': enum('none','load', 'trigger') # 'none': no pre-processing
                                                     # 'load': load analysis results
                                                     # 'trigger': trigger computation
    """


@schema
class Preprocess(dj.Imported):
    """
    A processing table to handle each PreprocessTask:
    + If `task_mode == "none"`: no pre-processing performed
    + If `task_mode == "trigger"`: Not implemented
    + If `task_mode == "load"`: Not implemented
    """

    definition = """
    -> PreprocessTask
    ---
    preprocess_time=null: datetime  # time of generation of pre-processing results 
    package_version='': varchar(16)
    """

    def make(self, key):
        task_mode, output_dir = (PreprocessTask & key).fetch1(
            "task_mode", "preprocess_output_dir"
        )
        preprocess_output_dir = find_full_path(get_imaging_root_data_dir(), output_dir)

        if task_mode == "none":
            print(f"No pre-processing run on entry: {key}")
        elif task_mode in ["load", "trigger"]:
            raise NotImplementedError(
                "Pre-processing steps are not implemented."
                "Please overwrite this `make` function with"
                "desired pre-processing steps."
            )
        else:
            raise ValueError(f"Unknown task mode: {task_mode}")

        self.insert1(key)


@schema
class ProcessingMethod(dj.Lookup):
    definition = """
    # Method, package, analysis suite used for processing of calcium imaging
    # data (e.g. Suite2p, CaImAn, etc.)
    processing_method: char(8)
    ---
    processing_method_desc: varchar(1000)
    """

    contents = [
        ("suite2p", "suite2p analysis suite"),
        ("caiman", "caiman analysis suite"),
    ]


@schema
class ProcessingParamSet(dj.Lookup):
    definition = """  #  Parameter set used for processing of calcium imaging data
    paramset_idx:  smallint
    ---
    -> ProcessingMethod
    paramset_desc: varchar(128)
    param_set_hash: uuid
    unique index (param_set_hash)
    params: longblob  # dictionary of all applicable parameters
    """

    @classmethod
    def insert_new_params(
        cls, processing_method: str, paramset_idx: int, paramset_desc: str, params: dict
    ):
        param_dict = {
            "processing_method": processing_method,
            "paramset_idx": paramset_idx,
            "paramset_desc": paramset_desc,
            "params": params,
            "param_set_hash": dict_to_uuid(params),
        }
        q_param = cls & {"param_set_hash": param_dict["param_set_hash"]}

        if q_param:  # If the specified param-set already exists
            pname = q_param.fetch1("paramset_idx")
            if pname == paramset_idx:  # If the existed set has the same name: job done
                return
            else:  # If not same name: human error, trying to add the same paramset with different name
                raise dj.DataJointError(
                    "The specified param-set already exists - name: {}".format(pname)
                )
        else:
            cls.insert1(param_dict)


@schema
class CellCompartment(dj.Lookup):
    definition = """  # Cell compartments that can be imaged
    cell_compartment         : char(16)
    """

    contents = zip(["axon", "soma", "bouton"])


@schema
class MaskType(dj.Lookup):
    definition = """ # Possible classifications for a segmented mask
    mask_type        : varchar(16)
    """

    contents = zip(["soma", "axon", "dendrite", "neuropil", "artefact", "unknown"])


# -------------- Trigger a processing routine --------------


@schema
class ProcessingTask(dj.Manual):
    definition = """  # Manual table for defining a processing task ready to be run
    -> Preprocess
    -> ProcessingParamSet
    ---
    processing_output_dir: varchar(255)         #  output directory of the processed scan relative to root data directory
    task_mode='load': enum('load', 'trigger')   # 'load': load computed analysis results, 'trigger': trigger computation
    """

    @classmethod
    def infer_output_dir(cls, key, relative=False, mkdir=False):
        """
        Given a 'key' to an entry in this table
        Return the expected processing_output_dir based on the following convention:
            processed_dir / scan_dir / {processing_method}_{paramset_idx}
            e.g.: sub4/sess1/scan0/suite2p_0
        """
        image_locators = {
            "NIS": get_nd2_files,
            "ScanImage": get_scan_image_files,
            "Scanbox": get_scan_box_files,
        }
        image_locator = image_locators[(scan.Scan & key).fetch1("acq_software")]

        scan_dir = find_full_path(
            get_imaging_root_data_dir(), image_locator(key)[0]
        ).parent
        root_dir = find_root_directory(get_imaging_root_data_dir(), scan_dir)

        method = (
            (ProcessingParamSet & key).fetch1("processing_method").replace(".", "-")
        )

        processed_dir = pathlib.Path(get_processed_root_data_dir())
        output_dir = (
            processed_dir
            / scan_dir.relative_to(root_dir)
            / f'{method}_{key["paramset_idx"]}'
        )

        if mkdir:
            output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir.relative_to(processed_dir) if relative else output_dir

    @classmethod
    def generate(cls, scan_key, paramset_idx=0):
        """
        Method to auto-generate ProcessingTask entries for a particular Scan using the specified parameter set.
        """
        key = {**scan_key, "paramset_idx": paramset_idx}

        output_dir = cls.infer_output_dir(key, relative=False, mkdir=True)

        method = (ProcessingParamSet & {"paramset_idx": paramset_idx}).fetch1(
            "processing_method"
        )

        try:
            if method == "suite2p":
                from element_interface import suite2p_loader

                suite2p_loader.Suite2p(output_dir)
            elif method == "caiman":
                from element_interface import caiman_loader

                caiman_loader.CaImAn(output_dir)
            else:
                raise NotImplementedError(
                    "Unknown/unimplemented method: {}".format(method)
                )
        except FileNotFoundError:
            task_mode = "trigger"
        else:
            task_mode = "load"

        cls.insert1(
            {
                **key,
                "processing_output_dir": output_dir,
                "task_mode": task_mode,
            }
        )

    auto_generate_entries = generate


@schema
class Processing(dj.Computed):
    definition = """  # Processing Procedure
    -> ProcessingTask
    ---
    processing_time     : datetime  # time of generation of this set of processed, segmented results
    package_version=''  : varchar(16)
    """

    # Run processing only on Scan with ScanInfo inserted
    @property
    def key_source(self):
        return ProcessingTask & scan.ScanInfo

    def make(self, key):
        task_mode, output_dir = (ProcessingTask & key).fetch1(
            "task_mode", "processing_output_dir"
        )

        output_dir = find_full_path(get_imaging_root_data_dir(), output_dir).as_posix()
        if not output_dir:
            output_dir = ProcessingTask.infer_output_dir(key, relative=True, mkdir=True)
            # update processing_output_dir
            ProcessingTask.update1(
                {**key, "processing_output_dir": output_dir.as_posix()}
            )

        if task_mode == "load":
            method, imaging_dataset = get_loader_result(key, ProcessingTask)
            if method == "suite2p":
                if (scan.ScanInfo & key).fetch1("nrois") > 0:
                    raise NotImplementedError(
                        f"Suite2p ingestion error - Unable to handle"
                        f" ScanImage multi-ROI scanning mode yet"
                    )
                suite2p_dataset = imaging_dataset
                key = {**key, "processing_time": suite2p_dataset.creation_time}
            elif method == "caiman":
                caiman_dataset = imaging_dataset
                key = {**key, "processing_time": caiman_dataset.creation_time}
            else:
                raise NotImplementedError("Unknown method: {}".format(method))
        elif task_mode == "trigger":

            method = (ProcessingParamSet * ProcessingTask & key).fetch1(
                "processing_method"
            )

            preprocess_paramsets = (
                PreprocessParamSteps.Step()
                & dict(preprocess_param_steps_id=key["preprocess_param_steps_id"])
            ).fetch("paramset_idx")

            if len(preprocess_paramsets) == 0:
                # No pre-processing steps were performed on the acquired dataset, so process the raw/acquired files.
                image_files = (scan.ScanInfo.ScanFile & key).fetch("file_path")
                image_files = [
                    find_full_path(get_imaging_root_data_dir(), image_file)
                    for image_file in image_files
                ]

            else:
                preprocess_output_dir = (PreprocessTask & key).fetch1(
                    "preprocess_output_dir"
                )

                preprocess_output_dir = find_full_path(
                    get_imaging_root_data_dir(), preprocess_output_dir
                )

                if not preprocess_output_dir.exists():
                    raise FileNotFoundError(
                        f"Pre-processed output directory not found ({preprocess_output_dir})"
                    )

                image_files = list(preprocess_output_dir.glob("*.tif"))

            if method == "suite2p":
                import suite2p

                suite2p_params = (ProcessingTask * ProcessingParamSet & key).fetch1(
                    "params"
                )
                suite2p_params["save_path0"] = output_dir
                suite2p_params["fs"] = (scan.ScanInfo & key).fetch1("fps")

                input_format = pathlib.Path(image_files[0]).suffix
                suite2p_params["input_format"] = input_format[1:]

                suite2p_paths = {
                    "data_path": [image_files[0].parent.as_posix()],
                    "tiff_list": [f.as_posix() for f in image_files],
                }

                suite2p.run_s2p(ops=suite2p_params, db=suite2p_paths)  # Run suite2p

                _, imaging_dataset = get_loader_result(key, ProcessingTask)
                suite2p_dataset = imaging_dataset
                key = {**key, "processing_time": suite2p_dataset.creation_time}

            elif method == "caiman":
                from element_interface.run_caiman import run_caiman

                caiman_params = (ProcessingTask * ProcessingParamSet & key).fetch1(
                    "params"
                )
                sampling_rate, ndepths = (scan.ScanInfo & key).fetch1("fps", "ndepths")

                is3D = bool(ndepths > 1)
                if is3D:
                    raise NotImplementedError(
                        "Caiman pipeline is not yet capable of analyzing 3D scans."
                    )
                run_caiman(
                    file_paths=[f.as_posix() for f in image_files],
                    parameters=caiman_params,
                    sampling_rate=sampling_rate,
                    output_dir=output_dir,
                    is3D=is3D,
                )

                _, imaging_dataset = get_loader_result(key, ProcessingTask)
                caiman_dataset = imaging_dataset
                key["processing_time"] = caiman_dataset.creation_time

        else:
            raise ValueError(f"Unknown task mode: {task_mode}")

        self.insert1(key)


@schema
class Curation(dj.Manual):
    definition = """  #  Curation(s) performed on processing results (including none)
    -> Processing
    curation_id: int
    ---
    curation_time: datetime             # time of generation of this set of curated results 
    curation_output_dir: varchar(255)   # output directory of the curated results, relative to root data directory
    manual_curation: bool               # has manual curation been performed on this result?
    curation_note='': varchar(2000)  
    """

    def create1_from_processing_task(self, key, is_curated=False, curation_note=""):
        """
        A convenient function to create a new corresponding "Curation" for a particular "ProcessingTask"
        """
        if key not in Processing():
            raise ValueError(
                f"No corresponding entry in Processing available for: {key};"
                f"Please run `Processing.populate(key)`"
            )

        output_dir = (ProcessingTask & key).fetch1("processing_output_dir")
        method, imaging_dataset = get_loader_result(key, ProcessingTask)

        if method == "suite2p":
            suite2p_dataset = imaging_dataset
            curation_time = suite2p_dataset.creation_time
        elif method == "caiman":
            caiman_dataset = imaging_dataset
            curation_time = caiman_dataset.creation_time
        else:
            raise NotImplementedError("Unknown method: {}".format(method))

        # Synthesize curation_id
        curation_id = (
            dj.U().aggr(self & key, n="ifnull(max(curation_id)+1,1)").fetch1("n")
        )
        self.insert1(
            {
                **key,
                "curation_id": curation_id,
                "curation_time": curation_time,
                "curation_output_dir": output_dir,
                "manual_curation": is_curated,
                "curation_note": curation_note,
            }
        )


# -------------- Motion Correction --------------


@schema
class MotionCorrection(dj.Imported):
    definition = """  #  Results of motion correction performed on the imaging data
    -> Curation
    ---
    -> scan.Channel.proj(motion_correct_channel='channel') # channel used for motion correction in this processing task
    """

    class RigidMotionCorrection(dj.Part):
        definition = """  # Details of rigid motion correction performed on the imaging data
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

        definition = """  # Details of non-rigid motion correction performed on the imaging data
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
        definition = """ # Summary images for each field and channel after corrections
        -> master
        -> scan.ScanInfo.Field
        ---
        ref_image               : longblob  # image used as alignment template
        average_image           : longblob  # mean of registered frames
        correlation_image=null  : longblob  # correlation map (computed during cell detection)
        max_proj_image=null     : longblob  # max of registered frames
        """

    def make(self, key):
        method, imaging_dataset = get_loader_result(key, Curation)

        field_keys, _ = (scan.ScanInfo.Field & key).fetch(
            "KEY", "field_z", order_by="field_z"
        )

        if method == "suite2p":
            suite2p_dataset = imaging_dataset

            motion_correct_channel = suite2p_dataset.planes[0].alignment_channel

            # ---- iterate through all s2p plane outputs ----
            rigid_correction, nonrigid_correction, nonrigid_blocks = {}, {}, {}
            summary_images = []
            for idx, (plane, s2p) in enumerate(suite2p_dataset.planes.items()):
                # -- rigid motion correction --
                if idx == 0:
                    rigid_correction = {
                        **key,
                        "y_shifts": s2p.ops["yoff"],
                        "x_shifts": s2p.ops["xoff"],
                        "z_shifts": np.full_like(s2p.ops["xoff"], 0),
                        "y_std": np.nanstd(s2p.ops["yoff"]),
                        "x_std": np.nanstd(s2p.ops["xoff"]),
                        "z_std": np.nan,
                        "outlier_frames": s2p.ops["badframes"],
                    }
                else:
                    rigid_correction["y_shifts"] = np.vstack(
                        [rigid_correction["y_shifts"], s2p.ops["yoff"]]
                    )
                    rigid_correction["y_std"] = np.nanstd(
                        rigid_correction["y_shifts"].flatten()
                    )
                    rigid_correction["x_shifts"] = np.vstack(
                        [rigid_correction["x_shifts"], s2p.ops["xoff"]]
                    )
                    rigid_correction["x_std"] = np.nanstd(
                        rigid_correction["x_shifts"].flatten()
                    )
                    rigid_correction["outlier_frames"] = np.logical_or(
                        rigid_correction["outlier_frames"], s2p.ops["badframes"]
                    )
                # -- non-rigid motion correction --
                if s2p.ops["nonrigid"]:
                    if idx == 0:
                        nonrigid_correction = {
                            **key,
                            "block_height": s2p.ops["block_size"][0],
                            "block_width": s2p.ops["block_size"][1],
                            "block_depth": 1,
                            "block_count_y": s2p.ops["nblocks"][0],
                            "block_count_x": s2p.ops["nblocks"][1],
                            "block_count_z": len(suite2p_dataset.planes),
                            "outlier_frames": s2p.ops["badframes"],
                        }
                    else:
                        nonrigid_correction["outlier_frames"] = np.logical_or(
                            nonrigid_correction["outlier_frames"], s2p.ops["badframes"]
                        )
                    for b_id, (b_y, b_x, bshift_y, bshift_x) in enumerate(
                        zip(
                            s2p.ops["xblock"],
                            s2p.ops["yblock"],
                            s2p.ops["yoff1"].T,
                            s2p.ops["xoff1"].T,
                        )
                    ):
                        if b_id in nonrigid_blocks:
                            nonrigid_blocks[b_id]["y_shifts"] = np.vstack(
                                [nonrigid_blocks[b_id]["y_shifts"], bshift_y]
                            )
                            nonrigid_blocks[b_id]["y_std"] = np.nanstd(
                                nonrigid_blocks[b_id]["y_shifts"].flatten()
                            )
                            nonrigid_blocks[b_id]["x_shifts"] = np.vstack(
                                [nonrigid_blocks[b_id]["x_shifts"], bshift_x]
                            )
                            nonrigid_blocks[b_id]["x_std"] = np.nanstd(
                                nonrigid_blocks[b_id]["x_shifts"].flatten()
                            )
                        else:
                            nonrigid_blocks[b_id] = {
                                **key,
                                "block_id": b_id,
                                "block_y": b_y,
                                "block_x": b_x,
                                "block_z": np.full_like(b_x, plane),
                                "y_shifts": bshift_y,
                                "x_shifts": bshift_x,
                                "z_shifts": np.full(
                                    (len(suite2p_dataset.planes), len(bshift_x)), 0
                                ),
                                "y_std": np.nanstd(bshift_y),
                                "x_std": np.nanstd(bshift_x),
                                "z_std": np.nan,
                            }

                # -- summary images --
                motion_correction_key = (
                    scan.ScanInfo.Field * Curation & key & field_keys[plane]
                ).fetch1("KEY")
                summary_images.append(
                    {
                        **motion_correction_key,
                        "ref_image": s2p.ref_image,
                        "average_image": s2p.mean_image,
                        "correlation_image": s2p.correlation_map,
                        "max_proj_image": s2p.max_proj_image,
                    }
                )

            self.insert1({**key, "motion_correct_channel": motion_correct_channel})
            if rigid_correction:
                self.RigidMotionCorrection.insert1(rigid_correction)
            if nonrigid_correction:
                self.NonRigidMotionCorrection.insert1(nonrigid_correction)
                self.Block.insert(nonrigid_blocks.values())
            self.Summary.insert(summary_images)
        elif method == "caiman":
            caiman_dataset = imaging_dataset

            self.insert1(
                {**key, "motion_correct_channel": caiman_dataset.alignment_channel}
            )

            is3D = caiman_dataset.params.motion["is3D"]
            if not caiman_dataset.params.motion["pw_rigid"]:
                # -- rigid motion correction --
                rigid_correction = {
                    **key,
                    "x_shifts": caiman_dataset.motion_correction["shifts_rig"][:, 0],
                    "y_shifts": caiman_dataset.motion_correction["shifts_rig"][:, 1],
                    "z_shifts": (
                        caiman_dataset.motion_correction["shifts_rig"][:, 2]
                        if is3D
                        else np.full_like(
                            caiman_dataset.motion_correction["shifts_rig"][:, 0], 0
                        )
                    ),
                    "x_std": np.nanstd(
                        caiman_dataset.motion_correction["shifts_rig"][:, 0]
                    ),
                    "y_std": np.nanstd(
                        caiman_dataset.motion_correction["shifts_rig"][:, 1]
                    ),
                    "z_std": (
                        np.nanstd(caiman_dataset.motion_correction["shifts_rig"][:, 2])
                        if is3D
                        else np.nan
                    ),
                    "outlier_frames": None,
                }

                self.RigidMotionCorrection.insert1(rigid_correction)
            else:
                # -- non-rigid motion correction --
                nonrigid_correction = {
                    **key,
                    "block_height": (
                        caiman_dataset.params.motion["strides"][0]
                        + caiman_dataset.params.motion["overlaps"][0]
                    ),
                    "block_width": (
                        caiman_dataset.params.motion["strides"][1]
                        + caiman_dataset.params.motion["overlaps"][1]
                    ),
                    "block_depth": (
                        caiman_dataset.params.motion["strides"][2]
                        + caiman_dataset.params.motion["overlaps"][2]
                        if is3D
                        else 1
                    ),
                    "block_count_x": len(
                        set(caiman_dataset.motion_correction["coord_shifts_els"][:, 0])
                    ),
                    "block_count_y": len(
                        set(caiman_dataset.motion_correction["coord_shifts_els"][:, 2])
                    ),
                    "block_count_z": (
                        len(
                            set(
                                caiman_dataset.motion_correction["coord_shifts_els"][
                                    :, 4
                                ]
                            )
                        )
                        if is3D
                        else 1
                    ),
                    "outlier_frames": None,
                }

                nonrigid_blocks = []
                for b_id in range(
                    len(caiman_dataset.motion_correction["x_shifts_els"][0, :])
                ):
                    nonrigid_blocks.append(
                        {
                            **key,
                            "block_id": b_id,
                            "block_x": np.arange(
                                *caiman_dataset.motion_correction["coord_shifts_els"][
                                    b_id, 0:2
                                ]
                            ),
                            "block_y": np.arange(
                                *caiman_dataset.motion_correction["coord_shifts_els"][
                                    b_id, 2:4
                                ]
                            ),
                            "block_z": (
                                np.arange(
                                    *caiman_dataset.motion_correction[
                                        "coord_shifts_els"
                                    ][b_id, 4:6]
                                )
                                if is3D
                                else np.full_like(
                                    np.arange(
                                        *caiman_dataset.motion_correction[
                                            "coord_shifts_els"
                                        ][b_id, 0:2]
                                    ),
                                    0,
                                )
                            ),
                            "x_shifts": caiman_dataset.motion_correction[
                                "x_shifts_els"
                            ][:, b_id],
                            "y_shifts": caiman_dataset.motion_correction[
                                "y_shifts_els"
                            ][:, b_id],
                            "z_shifts": (
                                caiman_dataset.motion_correction["z_shifts_els"][
                                    :, b_id
                                ]
                                if is3D
                                else np.full_like(
                                    caiman_dataset.motion_correction["x_shifts_els"][
                                        :, b_id
                                    ],
                                    0,
                                )
                            ),
                            "x_std": np.nanstd(
                                caiman_dataset.motion_correction["x_shifts_els"][
                                    :, b_id
                                ]
                            ),
                            "y_std": np.nanstd(
                                caiman_dataset.motion_correction["y_shifts_els"][
                                    :, b_id
                                ]
                            ),
                            "z_std": (
                                np.nanstd(
                                    caiman_dataset.motion_correction["z_shifts_els"][
                                        :, b_id
                                    ]
                                )
                                if is3D
                                else np.nan
                            ),
                        }
                    )

                self.NonRigidMotionCorrection.insert1(nonrigid_correction)
                self.Block.insert(nonrigid_blocks)

            # -- summary images --
            summary_images = [
                {
                    **key,
                    **fkey,
                    "ref_image": ref_image,
                    "average_image": ave_img,
                    "correlation_image": corr_img,
                    "max_proj_image": max_img,
                }
                for fkey, ref_image, ave_img, corr_img, max_img in zip(
                    field_keys,
                    caiman_dataset.motion_correction["reference_image"].transpose(
                        2, 0, 1
                    )
                    if is3D
                    else caiman_dataset.motion_correction["reference_image"][...][
                        np.newaxis, ...
                    ],
                    caiman_dataset.motion_correction["average_image"].transpose(2, 0, 1)
                    if is3D
                    else caiman_dataset.motion_correction["average_image"][...][
                        np.newaxis, ...
                    ],
                    caiman_dataset.motion_correction["correlation_image"].transpose(
                        2, 0, 1
                    )
                    if is3D
                    else caiman_dataset.motion_correction["correlation_image"][...][
                        np.newaxis, ...
                    ],
                    caiman_dataset.motion_correction["max_image"].transpose(2, 0, 1)
                    if is3D
                    else caiman_dataset.motion_correction["max_image"][...][
                        np.newaxis, ...
                    ],
                )
            ]
            self.Summary.insert(summary_images)
        else:
            raise NotImplementedError("Unknown/unimplemented method: {}".format(method))


# -------------- Segmentation --------------


@schema
class Segmentation(dj.Computed):
    definition = """ # Different mask segmentations.
    -> Curation
    """

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
        method, imaging_dataset = get_loader_result(key, Curation)

        if method == "suite2p":
            suite2p_dataset = imaging_dataset

            # ---- iterate through all s2p plane outputs ----
            masks, cells = [], []
            for plane, s2p in suite2p_dataset.planes.items():
                mask_count = len(masks)  # increment mask id from all "plane"
                for mask_idx, (is_cell, cell_prob, mask_stat) in enumerate(
                    zip(s2p.iscell, s2p.cell_prob, s2p.stat)
                ):
                    masks.append(
                        {
                            **key,
                            "mask": mask_idx + mask_count,
                            "segmentation_channel": s2p.segmentation_channel,
                            "mask_npix": mask_stat["npix"],
                            "mask_center_x": mask_stat["med"][1],
                            "mask_center_y": mask_stat["med"][0],
                            "mask_center_z": mask_stat.get("iplane", plane),
                            "mask_xpix": mask_stat["xpix"],
                            "mask_ypix": mask_stat["ypix"],
                            "mask_zpix": np.full(
                                mask_stat["npix"], mask_stat.get("iplane", plane)
                            ),
                            "mask_weights": mask_stat["lam"],
                        }
                    )
                    if is_cell:
                        cells.append(
                            {
                                **key,
                                "mask_classification_method": "suite2p_default_classifier",
                                "mask": mask_idx + mask_count,
                                "mask_type": "soma",
                                "confidence": cell_prob,
                            }
                        )

            self.insert1(key)
            self.Mask.insert(masks, ignore_extra_fields=True)

            if cells:
                MaskClassification.insert1(
                    {**key, "mask_classification_method": "suite2p_default_classifier"},
                    allow_direct_insert=True,
                )
                MaskClassification.MaskType.insert(
                    cells, ignore_extra_fields=True, allow_direct_insert=True
                )
        elif method == "caiman":
            caiman_dataset = imaging_dataset

            # infer "segmentation_channel" - from params if available, else from caiman loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1("params")
            segmentation_channel = params.get(
                "segmentation_channel", caiman_dataset.segmentation_channel
            )

            masks, cells = [], []
            for mask in caiman_dataset.masks:
                masks.append(
                    {
                        **key,
                        "segmentation_channel": segmentation_channel,
                        "mask": mask["mask_id"],
                        "mask_npix": mask["mask_npix"],
                        "mask_center_x": mask["mask_center_x"],
                        "mask_center_y": mask["mask_center_y"],
                        "mask_center_z": mask["mask_center_z"],
                        "mask_xpix": mask["mask_xpix"],
                        "mask_ypix": mask["mask_ypix"],
                        "mask_zpix": mask["mask_zpix"],
                        "mask_weights": mask["mask_weights"],
                    }
                )
                if caiman_dataset.cnmf.estimates.idx_components is not None:
                    if mask["mask_id"] in caiman_dataset.cnmf.estimates.idx_components:
                        cells.append(
                            {
                                **key,
                                "mask_classification_method": "caiman_default_classifier",
                                "mask": mask["mask_id"],
                                "mask_type": "soma",
                            }
                        )

            self.insert1(key)
            self.Mask.insert(masks, ignore_extra_fields=True)

            if cells:
                MaskClassification.insert1(
                    {**key, "mask_classification_method": "caiman_default_classifier"},
                    allow_direct_insert=True,
                )
                MaskClassification.MaskType.insert(
                    cells, ignore_extra_fields=True, allow_direct_insert=True
                )
        else:
            raise NotImplementedError(f"Unknown/unimplemented method: {method}")


@schema
class MaskClassificationMethod(dj.Lookup):
    definition = """
    mask_classification_method: varchar(48)
    """

    contents = zip(["suite2p_default_classifier", "caiman_default_classifier"])


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
        method, imaging_dataset = get_loader_result(key, Curation)

        if method == "suite2p":
            suite2p_dataset = imaging_dataset

            # ---- iterate through all s2p plane outputs ----
            fluo_traces, fluo_chn2_traces = [], []
            for s2p in suite2p_dataset.planes.values():
                mask_count = len(fluo_traces)  # increment mask id from all "plane"
                for mask_idx, (f, fneu) in enumerate(zip(s2p.F, s2p.Fneu)):
                    fluo_traces.append(
                        {
                            **key,
                            "mask": mask_idx + mask_count,
                            "fluo_channel": 0,
                            "fluorescence": f,
                            "neuropil_fluorescence": fneu,
                        }
                    )
                if len(s2p.F_chan2):
                    mask_chn2_count = len(
                        fluo_chn2_traces
                    )  # increment mask id from all planes
                    for mask_idx, (f2, fneu2) in enumerate(
                        zip(s2p.F_chan2, s2p.Fneu_chan2)
                    ):
                        fluo_chn2_traces.append(
                            {
                                **key,
                                "mask": mask_idx + mask_chn2_count,
                                "fluo_channel": 1,
                                "fluorescence": f2,
                                "neuropil_fluorescence": fneu2,
                            }
                        )

            self.insert1(key)
            self.Trace.insert(fluo_traces + fluo_chn2_traces)
        elif method == "caiman":
            caiman_dataset = imaging_dataset

            # infer "segmentation_channel" - from params if available, else from caiman loader
            params = (ProcessingParamSet * ProcessingTask & key).fetch1("params")
            segmentation_channel = params.get(
                "segmentation_channel", caiman_dataset.segmentation_channel
            )

            fluo_traces = []
            for mask in caiman_dataset.masks:
                fluo_traces.append(
                    {
                        **key,
                        "mask": mask["mask_id"],
                        "fluo_channel": segmentation_channel,
                        "fluorescence": mask["inferred_trace"],
                    }
                )

            self.insert1(key)
            self.Trace.insert(fluo_traces)

        else:
            raise NotImplementedError("Unknown/unimplemented method: {}".format(method))


@schema
class ActivityExtractionMethod(dj.Lookup):
    definition = """
    extraction_method: varchar(32)
    """

    contents = zip(["suite2p_deconvolution", "caiman_deconvolution", "caiman_dff"])


@schema
class Activity(dj.Computed):
    definition = """
    # Inferred neural activity from fluorescence trace - e.g. dff, spikes
    -> Fluorescence
    -> ActivityExtractionMethod
    """

    class Trace(dj.Part):
        definition = """
        -> master
        -> Fluorescence.Trace
        ---
        activity_trace: longblob
        """

    @property
    def key_source(self):
        suite2p_key_source = (
            Fluorescence
            * ActivityExtractionMethod
            * ProcessingParamSet.proj("processing_method")
            & 'processing_method = "suite2p"'
            & 'extraction_method LIKE "suite2p%"'
        )
        caiman_key_source = (
            Fluorescence
            * ActivityExtractionMethod
            * ProcessingParamSet.proj("processing_method")
            & 'processing_method = "caiman"'
            & 'extraction_method LIKE "caiman%"'
        )
        return suite2p_key_source.proj() + caiman_key_source.proj()

    def make(self, key):
        method, imaging_dataset = get_loader_result(key, Curation)

        if method == "suite2p":
            if key["extraction_method"] == "suite2p_deconvolution":
                suite2p_dataset = imaging_dataset
                # ---- iterate through all s2p plane outputs ----
                spikes = [
                    dict(
                        key,
                        mask=mask_idx,
                        fluo_channel=0,
                        activity_trace=spks,
                    )
                    for mask_idx, spks in enumerate(
                        s
                        for plane in suite2p_dataset.planes.values()
                        for s in plane.spks
                    )
                ]

                self.insert1(key)
                self.Trace.insert(spikes)
        elif method == "caiman":
            caiman_dataset = imaging_dataset

            if key["extraction_method"] in ("caiman_deconvolution", "caiman_dff"):
                attr_mapper = {"caiman_deconvolution": "spikes", "caiman_dff": "dff"}

                # infer "segmentation_channel" - from params if available, else from caiman loader
                params = (ProcessingParamSet * ProcessingTask & key).fetch1("params")
                segmentation_channel = params.get(
                    "segmentation_channel", caiman_dataset.segmentation_channel
                )

                self.insert1(key)
                self.Trace.insert(
                    dict(
                        key,
                        mask=mask["mask_id"],
                        fluo_channel=segmentation_channel,
                        activity_trace=mask[attr_mapper[key["extraction_method"]]],
                    )
                    for mask in caiman_dataset.masks
                )
        else:
            raise NotImplementedError("Unknown/unimplemented method: {}".format(method))


# ---------------- HELPER FUNCTIONS ----------------


_table_attribute_mapper = {
    "ProcessingTask": "processing_output_dir",
    "Curation": "curation_output_dir",
}


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
        "processing_method", _table_attribute_mapper[table.__name__]
    )

    output_path = find_full_path(get_imaging_root_data_dir(), output_dir)

    if method == "suite2p":
        from element_interface import suite2p_loader

        loaded_dataset = suite2p_loader.Suite2p(output_path)
    elif method == "caiman":
        from element_interface import caiman_loader

        loaded_dataset = caiman_loader.CaImAn(output_path)
    else:
        raise NotImplementedError("Unknown/unimplemented method: {}".format(method))

    return method, loaded_dataset
