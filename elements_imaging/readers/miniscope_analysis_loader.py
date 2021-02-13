import numpy as np
import h5py
from datetime import datetime
import os
import pathlib

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
     - 'SFP.mat':                       Segmentations
     - 'ms.mat':
     - 'ms[Options]':                   Input parameters
     - 'ms[meanFrame]':
     - 'ms[CorrProj]':
     - 'ms[PeaktoNoiseProj]':
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
          self.ref_image = None                                # TODO
          self.average_image = self.mat_ms['meanFrame']        # TODO
          self.correlation_map = self.mat_ms['CorrProj']       # TODO
          self.max_proj_image = self.mat_ms['PeaktoNoiseProj'] # TODO
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
          for i in range(np.shape(self.mat_ms['ms']['Centroids'])[1]): # TODO: determine mapping between centroids and traces
               center_z = 0 # TODO
               weights = # TODO
               xpix = # TODO
               ypix = # TODO
               zpix = np.full(len(weights), center_z) # TODO

               masks.append({'mask_id': i,
                              'mask_npix': len(weights), 
                              'mask_weights': weights,
                              'mask_center_x': self.mat_ms['ms']['Centroids'][0,i], 
                              'mask_center_y': self.mat_ms['ms']['Centroids'][1,i], 
                              'mask_center_z': center_z,
                              'mask_xpix': xpix, 
                              'mask_ypix': ypix, 
                              'mask_zpix': zpix,
                              'raw_trace': self.mat_ms['ms']['RawTraces'][i,:],
                              'dff': self.mat_ms['ms']['FiltTraces'][i,:],
                              'spikes': self.mat_ms['ms']['DeconvolvedTraces'][i,:]})
          return masks

