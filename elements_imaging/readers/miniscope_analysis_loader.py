import numpy as np
import h5py
from datetime import datetime
import os
import pathlib
import scipy

_required_mat_ms_fields = ['Options',
                           'meanFrame',
                           'CorrProj',
                           'PeaktoNoiseProj',
                           'RawTraces',
                           'FiltTraces',
                           'DeconvolvedTraces']


class MiniscopeAnalysis:
     """
     Parse the Miniscope Analysis output files
     Miniscope Analysis repository:     https://github.com/etterguillaume/MiniscopeAnalysis
     Expecting the following objects:
     - 'SFP.mat':                       Spatial footprints of the cells found while performing CNMFE extraction.
     - 'ms.mat':
     - 'ms[Options]':                   Parameters used to perform CNMFE.
     - 'ms[meanFrame]':
     - 'ms[CorrProj]':                  Correlation projection from the CNMFE.  Displays which pixels are correlated together and suggests the location of your cells.
     - 'ms[PeaktoNoiseProj]':           Peak-to-noise ratio of the correlation projection.  Gives you an idea of most prominent cells in your recording.
     - 'ms[RawTraces]':
     - 'ms[FiltTraces]':
     - 'ms[DeconvolvedTraces]':
     """

     def __init__(self, miniscope_analysis_dir):
          # ---- Search and verify Miniscope Analysis output file exists ----
          miniscope_analysis_dir = pathlib.Path(miniscope_analysis_dir)
          if not miniscope_analysis_dir.exists():
               raise FileNotFoundError(f'Miniscope Analysis directory not found: {miniscope_analysis_dir}')

          self.miniscope_fp_ms = f'{miniscope_analysis_dir}/ms.mat'
          self.miniscope_fp_sfp = f'{miniscope_analysis_dir}/SFP.mat'
          self.mat_ms = h5py.File(self.miniscope_fp_ms, 'r')
          self.mat_sfp = h5py.File(self.miniscope_fp_sfp, 'r')

          if not all(s in self.mat_ms for s in _required_mat_ms_fields):
               raise ValueError(f'Miniscope Analysis file {self.miniscope_fp_ms} does not have all required fields.')

          # ---- Initialize Miniscope Analysis results ----
          self.params = self.mat_ms['Options']
          self.average_image = self.mat_ms['meanFrame']
          self.correlation_image = self.mat_ms['CorrProj']
          self._masks = None

          # ---- Metainfo ----
          self.creation_time = datetime.fromtimestamp(os.stat(self.miniscope_fp_ms).st_ctime)
          self.curation_time = datetime.fromtimestamp(os.stat(self.miniscope_fp_ms).st_ctime)

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
          masks = []
          for i in range(int(self.mat_ms['ms']['numNeurons'][0,0])):
               center_y, center_x = scipy.ndimage.measurements.center_of_mass(self.mat_sfp[i,:,:])
               xpix, ypix, weights = scipy.sparse.find(self.mat_sfp[i,:,:])
                
               masks.append({'mask_id': i,
                              'mask_npix': len(weights), 
                              'mask_center_x': center_x,
                              'mask_center_y': center_y,
                              'mask_xpix': xpix, 
                              'mask_ypix': ypix, 
                              'mask_weights': weights,
                              'raw_trace': self.mat_ms['ms']['RawTraces'][i,:],
                              'dff': self.mat_ms['ms']['FiltTraces'][i,:],
                              'spikes': self.mat_ms['ms']['DeconvolvedTraces'][i,:]})
          return masks

