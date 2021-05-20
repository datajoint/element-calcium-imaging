import h5py
import caiman as cm
import scipy
import numpy as np
from datetime import datetime
import os
import pathlib
from tqdm import tqdm


_required_hdf5_fields = ['/motion_correction/reference_image',
                         '/motion_correction/correlation_image',
                         '/motion_correction/average_image',
                         '/motion_correction/max_image',
                         '/estimates/A']


class CaImAn:
    """
    Parse the CaImAn output file
    Expecting the following objects:
    - 'dims':
    - 'dview':
    - 'estimates':              Segmentations and traces
    - 'mmap_file':
    - 'params':                 Input parameters
    - 'remove_very_bad_comps':
    - 'skip_refinement':
    - 'motion_correction':      Motion correction shifts and summary images
    CaImAn results doc: https://caiman.readthedocs.io/en/master/Getting_Started.html#result-variables-for-2p-batch-analysis
    """

    def __init__(self, caiman_dir):
        # ---- Search and verify CaImAn output file exists ----
        caiman_dir = pathlib.Path(caiman_dir)
        if not caiman_dir.exists():
            raise FileNotFoundError('CaImAn directory not found: {}'.format(caiman_dir))

        for fp in caiman_dir.glob('*.hdf5'):
            with h5py.File(fp, 'r') as h5f:
                if all(s in h5f for s in _required_hdf5_fields):
                    self.caiman_fp = fp
                    break
        else:
            raise FileNotFoundError(
                'No CaImAn analysis output file found at {}'
                ' containg all required fields ({})'.format(caiman_dir, _required_hdf5_fields))

        # ---- Initialize CaImAn's results ----
        self.cnmf = cm.source_extraction.cnmf.cnmf.load_CNMF(self.caiman_fp)
        self.params = self.cnmf.params

        self.h5f = h5py.File(self.caiman_fp, 'r')
        self.package_version = self.h5f['params']['data']['caiman_version']
        self.motion_correction = self.h5f['motion_correction']
        self._masks = None

        # ---- Metainfo ----
        self.creation_time = datetime.fromtimestamp(os.stat(self.caiman_fp).st_ctime)
        self.curation_time = datetime.fromtimestamp(os.stat(self.caiman_fp).st_ctime)

    @property
    def masks(self):
        if self._masks is None:
            self._masks = self.extract_masks()
        return self._masks

    @property
    def alignment_channel(self):
        return 0  # hard-code to channel index 0

    @property
    def segmentation_channel(self):
        return 0  # hard-code to channel index 0

    def extract_masks(self):
        if self.params.motion['is3D']:
            raise NotImplemented('CaImAn mask extraction for volumetric data not yet implemented')

        comp_contours = cm.utils.visualization.get_contours(
            self.cnmf.estimates.A, self.cnmf.dims)

        masks = []
        for comp_idx, comp_contour in enumerate(comp_contours):
            ind, _, weights = scipy.sparse.find(self.cnmf.estimates.A[:, comp_idx])
            if self.cnmf.params.motion['is3D']:
                xpix, ypix, zpix = np.unravel_index(ind, self.cnmf.dims, order='F')
                center_x, center_y, center_z = comp_contour['CoM'].astype(int)
            else:
                xpix, ypix = np.unravel_index(ind, self.cnmf.dims, order='F')
                center_x, center_y = comp_contour['CoM'].astype(int)
                center_z = 0
                zpix = np.full(len(weights), center_z)

            masks.append({'mask_id': comp_contour['neuron_id'],
                          'mask_npix': len(weights), 'mask_weights': weights,
                          'mask_center_x': center_x,
                          'mask_center_y': center_y,
                          'mask_center_z': center_z,
                          'mask_xpix': xpix, 'mask_ypix': ypix, 'mask_zpix': zpix,
                          'inferred_trace': self.cnmf.estimates.C[comp_idx, :],
                          'dff': self.cnmf.estimates.F_dff[comp_idx, :],
                          'spikes': self.cnmf.estimates.S[comp_idx, :]})
        return masks


def _process_scanimage_tiff(scan_filenames, output_dir='./'):
    """
    Read ScanImage TIFF - reshape into volumetric data based on scanning depths and channels
    Save new TIFF files for each channel - with shape (frame x height x width x depth)
    """
    from skimage.external.tifffile import imsave
    import scanreader

    # ------------ CaImAn multi-channel multi-plane tiff file ------------
    for scan_filename in tqdm(scan_filenames):
        scan = scanreader.read_scan(scan_filename)
        cm_movie = cm.load(scan_filename)

        # ---- Volumetric movie: (depth x height x width x channel x frame) ----
        # tiff pages are ordered as:
        # ch0-pln0-t0, ch1-pln0-t0, ch0-pln1-t0, ch1-pln1-t0, ..., ch0-pln1-t5, ch1-pln1-t5, ...

        vol_timeseries = np.full((scan.num_scanning_depths,
                                  scan.image_height, scan.image_width,
                                scan.num_channels, scan.num_frames), 0).astype(scan.dtype)
        for pln_idx in range(scan.num_scanning_depths):
            for chn_idx in range(scan.num_channels):
                pln_chn_ind = np.arange(pln_idx * scan.num_channels + chn_idx,
                                        scan._num_pages,
                                        scan.num_scanning_depths * scan.num_channels)
                vol_timeseries[pln_idx, :, :, chn_idx, :] = cm_movie[pln_chn_ind, :, :].transpose(1, 2, 0)

        # save volumetric movie for individual channel
        output_dir = pathlib.Path(output_dir)
        fname = pathlib.Path(scan_filename).stem

        for chn_idx in range(scan.num_channels):
            if scan.num_scanning_depths == 1:
                chn_vol = vol_timeseries[0, :, :, chn_idx, :].squeeze().transpose(2, 0, 1)  # (frame x height x width)
            else:
                chn_vol = vol_timeseries[:, :, :, chn_idx, :].transpose(3, 1, 2, 0)  # (frame x height x width x depth)
            save_fp = output_dir / '{}_chn{}.tif'.format(fname, chn_idx)
            imsave(save_fp.as_posix(), chn_vol)


def _save_mc(mc, caiman_fp, is3D):
    """
    DataJoint Imaging Element - CaImAn Integration
    Run these commands after the CaImAn analysis has completed.
    This will save the relevant motion correction data into the '*.hdf5' file.
    Please do not clear variables from memory prior to running these commands.
    The motion correction (mc) object will be read from memory.

    'mc' :                CaImAn motion correction object
    'caiman_fp' :         CaImAn output (*.hdf5) file path

    'shifts_rig' :        Rigid transformation x and y shifts per frame
    'x_shifts_els' :      Non rigid transformation x shifts per frame per block
    'y_shifts_els' :      Non rigid transformation y shifts per frame per block
    """

    # Load motion corrected mmap image
    mc_image = cm.load(mc.mmap_file, is3D=is3D)

    # Compute motion corrected summary images
    average_image = np.mean(mc_image, axis=0)
    max_image = np.max(mc_image, axis=0)

    # Compute motion corrected correlation image
    correlation_image = cm.local_correlations(mc_image.transpose((1, 2, 3, 0)
                                                                 if is3D else (1, 2, 0)))
    correlation_image[np.isnan(correlation_image)] = 0

    # Compute mc.coord_shifts_els
    grid = []
    if is3D:
        for _, _, _, x, y, z, _ in cm.motion_correction.sliding_window_3d(
                mc_image[0, :, :, :], mc.overlaps, mc.strides):
            grid.append([x, x + mc.overlaps[0] + mc.strides[0],
                         y, y + mc.overlaps[1] + mc.strides[1],
                         z, z + mc.overlaps[2] + mc.strides[2]])
    else:
        for _, _, x, y, _ in cm.motion_correction.sliding_window(
                mc_image[0, :, :], mc.overlaps, mc.strides):
            grid.append([x, x + mc.overlaps[0] + mc.strides[0],
                         y, y + mc.overlaps[1] + mc.strides[1]])

    # Open hdf5 file and create 'motion_correction' group
    h5f = h5py.File(caiman_fp, 'r+')
    h5g = h5f.require_group("motion_correction")

    # Write motion correction shifts and motion corrected summary images to hdf5 file
    if mc.pw_rigid:
        h5g.require_dataset("x_shifts_els", shape=np.shape(mc.x_shifts_els),
                            data=mc.x_shifts_els,
                            dtype=mc.x_shifts_els[0][0].dtype)
        h5g.require_dataset("y_shifts_els", shape=np.shape(mc.y_shifts_els),
                            data=mc.y_shifts_els,
                            dtype=mc.y_shifts_els[0][0].dtype)
        if is3D:
            h5g.require_dataset("z_shifts_els", shape=np.shape(mc.z_shifts_els),
                                data=mc.z_shifts_els,
                                dtype=mc.z_shifts_els[0][0].dtype)

        h5g.require_dataset("coord_shifts_els", shape=np.shape(grid),
                            data=grid, dtype=type(grid[0][0]))

        # For CaImAn, reference image is still a 2D array even for the case of 3D
        # Assume that the same ref image is used for all the planes
        reference_image = np.tile(mc.total_template_els, (1, 1, correlation_image.shape[-1]))\
            if is3D else mc.total_template_els
    else:
        h5g.require_dataset("shifts_rig", shape=np.shape(mc.shifts_rig),
                            data=mc.shifts_rig, dtype=mc.shifts_rig[0][0].dtype)
        h5g.require_dataset("coord_shifts_rig", shape=np.shape(grid),
                            data=grid, dtype=type(grid[0][0]))
        reference_image = np.tile(mc.total_template_rig, (1, 1, correlation_image.shape[-1]))\
            if is3D else mc.total_template_rig

    h5g.require_dataset("reference_image", shape=np.shape(reference_image),
                        data=reference_image,
                        dtype=reference_image.dtype)
    h5g.require_dataset("correlation_image", shape=np.shape(correlation_image),
                        data=correlation_image,
                        dtype=correlation_image.dtype)
    h5g.require_dataset("average_image", shape=np.shape(average_image),
                        data=average_image, dtype=average_image.dtype)
    h5g.require_dataset("max_image", shape=np.shape(max_image),
                        data=max_image, dtype=max_image.dtype)

    # Close hdf5 file
    h5f.close()
