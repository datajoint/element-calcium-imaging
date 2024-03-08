import importlib
import inspect
import pathlib
from collections.abc import Callable
from datetime import datetime

import datajoint as dj
import numpy as np
from element_interface.utils import dict_to_uuid, find_full_path, find_root_directory

from . import scan
from .scan import (
    get_calcium_imaging_files,
    get_imaging_root_data_dir,
    get_processed_root_data_dir,
)

log = dj.logger()

schema = dj.schema()

imaging = None


def activate(
    schema_name,
    *,
    imaging_module,
    create_schema=True,
    create_tables=True,
):
    """
    activate(schema_name, *, create_schema=True, create_tables=True, activated_ephys=None)
        :param schema_name: schema name on the database server to activate the `spike_sorting` schema
        :param imaging_module: the activated imaging element for which this `processing` schema will be downstream from
        :param create_schema: when True (default), create schema in the database if it does not yet exist.
        :param create_tables: when True (default), create tables in the database if they do not yet exist.
    """
    global imaging
    imaging = imaging_module
    schema.activate(
        schema_name,
        create_schema=create_schema,
        create_tables=create_tables,
        add_objects=imaging.__dict__,
    )


# ---------------- Multi-plane Processing (per-plane basis) ----------------


# @schema
class FieldProcessingTask(dj.Computed):
    definition = """
    -> imaging.ProcessingTask
    field_idx: int
    ---
    params: longblob  # parameter set for this run
    processing_output_dir: varchar(1000)  #  Output directory of the processed scan relative to root data directory
    """

    def make(self, key):
        output_dir = (imaging.ProcessingTask & key).fetch1("processing_output_dir")
        output_dir = find_full_path(get_imaging_root_data_dir(), output_dir)

        method, params = (
            imaging.ProcessingTask * imaging.ProcessingParamSet & key
        ).fetch1("processing_method", "params")
        acq_software = (scan.Scan & key).fetch1("acq_software")

        field_ind = (scan.ScanInfo.Field & key).fetch("field_idx")
        sampling_rate, ndepths, nchannels, nfields, nrois = (
            scan.ScanInfo & key
        ).fetch1("fps", "ndepths", "nchannels", "nfields", "nrois")

        if method == "caiman" and acq_software == "PrairieView":
            from element_interface.prairie_view_loader import (
                PrairieViewMeta,
            )

            image_file = (scan.ScanInfo.ScanFile & key).fetch("file_path", limit=1)[0]
            pv_dir = pathlib.Path(image_file).parent
            PVmeta = PrairieViewMeta(pv_dir)

            channel = (
                params.get("channel_to_process", 0)
                if PVmeta.meta["num_channels"] > 1
                else PVmeta.meta["channels"][0]
            )

            field_processing_tasks = []
            for field_idx, plane_idx in zip(field_ind, PVmeta.meta["plane_indices"]):
                pln_output_dir = output_dir / f"pln{plane_idx}_chn{channel}"
                pln_output_dir.mkdir(parents=True, exist_ok=True)
                field_processing_tasks.append(
                    {
                        **key,
                        "field_idx": field_idx,
                        "params": {
                            **params,
                            "extra_dj_params": {
                                "channel": channel,
                                "plane_idx": plane_idx,
                            },
                        },
                        "processing_output_dir": pln_output_dir,
                    }
                )

        elif method == "suite2p" and acq_software == "ScanImage" and nrois > 0:
            import scanreader
            from suite2p import default_ops, io

            image_files = (scan.ScanInfo.ScanFile & key).fetch("file_path")
            image_files = [
                find_full_path(get_imaging_root_data_dir(), image_file).as_posix()
                for image_file in image_files
            ]

            scan_ = scanreader.read_scan(image_files)

            ops = {**default_ops(), **params}

            ops["save_path0"] = output_dir.as_posix()
            ops["save_folder"] = "suite2p"
            ops["fs"] = sampling_rate
            ops["nplanes"] = ndepths
            ops["nchannels"] = nchannels
            ops["input_format"] = pathlib.Path(image_files[0]).suffix[1:]
            ops["data_path"] = [pathlib.Path(image_files[0]).parent.as_posix()]
            ops["tiff_list"] = [f for f in image_files]
            ops["force_sktiff"] = False

            ops.update(
                {
                    "input_format": "mesoscan",
                    "nrois": nfields,
                    "dx": [],  # x-offset for each field
                    "dy": [],  # y-offset for each field
                    "slices": [],  # plane index for each field
                    "lines": [],  # row indices for each field
                }
            )
            for field_idx, field_info in enumerate(scan_.fields):
                ops["dx"].append(field_info.xslices[0].start)
                ops["dy"].append(field_info.yslices[0].start)
                ops["slices"].append(field_info.slice_id)
                ops["lines"].append(
                    np.arange(field_info.yslices[0].start, field_info.yslices[0].stop)
                )
                ops["extra_dj_params"] = {"field_idx": field_idx}

            # generate binary files for each field
            save_folder = output_dir / ops["save_folder"]
            save_folder.mkdir(exist_ok=True)
            _ = io.mesoscan_to_binary(ops.copy())

            ops_paths = [f for f in save_folder.rglob("plane*/ops.npy")]
            assert len(ops_paths) == nfields

            field_processing_tasks = []
            for ops_path in ops_paths:
                ops = np.load(ops_path, allow_pickle=True).item()
                ops["extra_dj_params"]["ops_path"] = ops_path.as_posix()
                field_processing_tasks.append(
                    {
                        **key,
                        "field_idx": ops["extra_dj_params"]["field_idx"],
                        "params": ops,
                        "processing_output_dir": ops_path.parent.as_posix(),
                    }
                )

        self.insert(field_processing_tasks, skip_duplicates=True)


# @schema
class FieldProcessing(dj.Computed):
    definition = """
    -> FieldProcessingTask
    ---
    execution_time: datetime   # datetime of the start of this step
    execution_duration: float  # (hour) execution duration
    """

    def make(self, key):
        execution_time = datetime.utcnow()

        output_dir, params = (FieldProcessingTask & key).fetch1(
            "processing_output_dir", "params"
        )
        extra_params = params.pop("extra_dj_params", {})
        output_dir = find_full_path(get_imaging_root_data_dir(), output_dir)

        acq_software = (scan.Scan & key).fetch1("acq_software")
        method = (imaging.ProcessingParamSet * imaging.ProcessingTask & key).fetch1(
            "processing_method"
        )
        sampling_rate = (scan.ScanInfo & key).fetch1("fps")

        if acq_software == "PrairieView" and method == "caiman":
            from element_interface.prairie_view_loader import PrairieViewMeta
            from element_interface.run_caiman import run_caiman

            image_file = (scan.ScanInfo.ScanFile & key).fetch("file_path", limit=1)[0]
            image_file = find_full_path(get_imaging_root_data_dir(), image_file)
            pv_dir = pathlib.Path(image_file).parent
            PVmeta = PrairieViewMeta(pv_dir)

            prepared_input_dir = output_dir.parent / "prepared_input"
            prepared_input_dir.mkdir(exist_ok=True)

            image_files = [
                PVmeta.write_single_bigtiff(
                    plane_idx=extra_params["plane_idx"],
                    channel=extra_params["channel"],
                    output_dir=prepared_input_dir,
                    caiman_compatible=True,
                )
            ]

            run_caiman(
                file_paths=[f.as_posix() for f in image_files],
                parameters=params,
                sampling_rate=sampling_rate,
                output_dir=output_dir.as_posix(),
                is3D=False,
            )
        elif acq_software == "ScanImage" and method == "suite2p":
            from suite2p.run_s2p import run_plane

            run_plane(params, ops_path=extra_params["ops_path"])
        else:
            raise NotImplementedError(
                f"Field processing for {acq_software} scans with {method} is not yet supported in this table."
            )

        exec_dur = (datetime.utcnow() - execution_time).total_seconds() / 3600
        self.insert1(
            {
                **key,
                "execution_time": execution_time,
                "execution_duration": exec_dur,
            }
        )
