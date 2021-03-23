import numpy as np
import pathlib
from datetime import datetime
from collections import OrderedDict


_suite2p_ftypes = ('ops', 'Fneu', 'Fneu_chan2', 'F', 'F_chan2',
                   'iscell', 'spks', 'stat', 'redcell')


class Suite2p:
    """
    Wrapper class containing all suite2p outputs from one suite2p analysis routine.
    This includes outputs from the individual plane, with plane indexing starting from 0
    Plane index of -1 indicates a suite2p "combined" outputs from all planes,
     thus saved in the "planes_combined" attribute

    A 'suite2p_dir' example:

        -- suite2p_dir
          -- plane0
             -- ops.npy
             -- F.npy
             -- ...
          -- plane1
             -- ops.npy
             -- F.npy
             -- ...
          -- combined
             -- ops.npy
             -- F.npy
             -- ...
    """

    def __init__(self, suite2p_dir):
        self.suite2p_dir = pathlib.Path(suite2p_dir)

        ops_filepaths = list(self.suite2p_dir.rglob('*ops.npy'))

        if not len(ops_filepaths):
            raise FileNotFoundError(
                'Suite2p output result files not found at {}'.format(suite2p_dir))

        self.planes = {}
        self.planes_combined = None
        for ops_fp in ops_filepaths:
            plane_s2p = PlaneSuite2p(ops_fp.parent)
            if plane_s2p.plane_idx == -1:
                self.planes_combined = plane_s2p
            else:
                self.planes[plane_s2p.plane_idx] = plane_s2p
        self.planes = OrderedDict({k: self.planes[k] for k in sorted(self.planes)})

        self.creation_time = min([p.creation_time for p in self.planes.values()])  # ealiest file creation time
        self.curation_time = max([p.curation_time for p in self.planes.values()])  # most recent curation time


class PlaneSuite2p:
    """
    Parse the suite2p output directory and load data, ***per plane***.
    Expecting the following files:
    - 'ops':        Options file
    - 'Fneu':       Neuropil traces file for functional channel
    - 'Fneu_chan2': Neuropil traces file for channel 2
    - 'F':          Fluorescence traces for functional channel
    - 'F_chan2':    Fluorescence traces for channel 2
    - 'iscell':     Array of (user curated) cells and probability of being a cell
    - 'spks':       Spikes (raw deconvolved with OASIS package)
    - 'stat':       Various statistics for each cell
    - 'redcell':    "Red cell" (second channel) stats

    Suite2p output doc: https://suite2p.readthedocs.io/en/latest/outputs.html
    """

    def __init__(self, suite2p_plane_dir):
        self.fpath = pathlib.Path(suite2p_plane_dir)

        # ---- Verify dataset exists ----
        ops_fp = self.fpath / 'ops.npy'
        if not ops_fp.exists():
            raise FileNotFoundError(
                'No "ops.npy" found. Invalid suite2p plane folder: {}'.format(self.fpath))
        self.creation_time = datetime.fromtimestamp(ops_fp.stat().st_ctime)

        iscell_fp = self.fpath / 'iscell.npy'
        if not iscell_fp.exists():
            raise FileNotFoundError(
                'No "iscell.npy" found. Invalid suite2p plane folder: {}'.format(self.fpath))
        self.curation_time = datetime.fromtimestamp(iscell_fp.stat().st_ctime)

        # ---- Initialize attributes ----
        for s2p_type in _suite2p_ftypes:
            setattr(self, '_{}'.format(s2p_type), None)
        self._cell_prob = None

        self.plane_idx = (-1 if self.fpath.name == 'combined'
                          else int(self.fpath.name.replace('plane', '')))

    # ---- load core files ----

    @property
    def ops(self):
        if self._ops is None:
            fp = self.fpath / 'ops.npy'
            self._ops = np.load(fp, allow_pickle=True).item()
        return self._ops

    @property
    def Fneu(self):
        if self._Fneu is None:
            fp = self.fpath / 'Fneu.npy'
            self._Fneu = np.load(fp) if fp.exists() else []
        return self._Fneu

    @property
    def Fneu_chan2(self):
        if self._Fneu_chan2 is None:
            fp = self.fpath / 'Fneu_chan2.npy'
            self._Fneu_chan2 = np.load(fp) if fp.exists() else []
        return self._Fneu_chan2

    @property
    def F(self):
        if self._F is None:
            fp = self.fpath / 'F.npy'
            self._F = np.load(fp) if fp.exists() else []
        return self._F

    @property
    def F_chan2(self):
        if self._F_chan2 is None:
            fp = self.fpath / 'F_chan2.npy'
            self._F_chan2 = np.load(fp) if fp.exists() else []
        return self._F_chan2

    @property
    def iscell(self):
        if self._iscell is None:
            fp = self.fpath / 'iscell.npy'
            d = np.load(fp)
            self._iscell = d[:, 0].astype(bool)
            self._cell_prob = d[:, 1]
        return self._iscell

    @property
    def cell_prob(self):
        if self._cell_prob is None:
            fp = self.fpath / 'iscell.npy'
            if fp.exists():
                d = np.load(fp)
                self._iscell = d[:, 0].astype(bool)
                self._cell_prob = d[:, 1]
        return self._cell_prob

    @property
    def spks(self):
        if self._spks is None:
            fp = self.fpath / 'spks.npy'
            self._spks = np.load(fp) if fp.exists() else []
        return self._spks

    @property
    def stat(self):
        if self._stat is None:
            fp = self.fpath / 'stat.npy'
            self._stat = np.load(fp, allow_pickle=True) if fp.exists() else []
        return self._stat

    @property
    def redcell(self):
        if self._redcell is None:
            fp = self.fpath / 'redcell.npy'
            self._redcell = np.load(fp) if fp.exists() else []
        return self._redcell

    # ---- image property ----

    @property
    def ref_image(self):
        return self.ops['refImg']

    @property
    def mean_image(self):
        return self.ops['meanImg']

    @property
    def max_proj_image(self):
        return self.ops.get('max_proj', np.full_like(self.mean_image, np.nan))

    @property
    def correlation_map(self):
        return self.ops['Vcorr']

    @property
    def alignment_channel(self):
        return self.ops['align_by_chan'] - 1  # suite2p is 1-based, convert to 0-based

    @property
    def segmentation_channel(self):
        return self.ops['functional_chan'] - 1  # suite2p is 1-based, convert to 0-based
