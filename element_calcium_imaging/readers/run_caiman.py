import cv2
import pathlib

try:
    cv2.setNumThreads(0)
except:
    pass

import caiman as cm
from caiman.source_extraction.cnmf.cnmf import *
from caiman.source_extraction.cnmf import params as params

from element_calcium_imaging.readers.caiman_loader import save_mc


def run_caiman(file_paths, parameters, sampling_rate, output_dir):
    """
    Runs the CNMF.fit_file analysis pipeline in caiman to do motion correction, memory mapping,
    patch based CNMF processing.

    Inputs
    ------
    file_paths: list
        list of full paths to files that need to be processed
    parameters: dict
        parameters
    sampling rate: float
        image sampling rate (Hz)
    output_dir: str
        output directory
    """
    parameters['fnames'] = file_paths
    parameters['fr'] = sampling_rate

    opts = params.CNMFParams(params_dict=parameters)

    c, dview, n_processes = cm.cluster.setup_cluster(
        backend='local', n_processes=None, single_thread=False)

    cnm = CNMF(n_processes, params=opts, dview=dview)
    cnmf_output, mc_output = cnm.fit_file(
        motion_correct=True, include_eval=True, output_dir=output_dir, return_mc=True)

    cm.stop_server(dview=dview)

    cnmf_output_file = pathlib.Path(cnmf_output.mmap_file[:-4] + 'hdf5')
    assert cnmf_output_file.exists()
    assert cnmf_output_file.parent == pathlib.Path(output_dir)

    print('cnmf_output_file: ', cnmf_output_file.as_posix())

    save_mc(mc_output, cnmf_output_file.as_posix(), parameters['is3D'])
