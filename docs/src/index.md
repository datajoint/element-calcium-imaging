# Element Calcium Imaging

This repository features DataJoint pipeline design for Functional Calcium imaging 
with `ScanImage`, `Scanbox`, or `Nikon NIS` acquisition system and `Suite2p` or `CaImAn` suites for analysis.

The element itself is comprised of two schemas, `scan` and `imaging`.  To handle
several use cases of this pipeline, we have designed two alternatives to `imaging` schemas,
including `imaging_no_curation` and `imaging_preprocess`. For more information on the Functional Calcium Imaging
and the development of the Element, see the [concepts page](./concepts.md). 

## Citation

If your work uses DataJoint Elements, please cite the following manuscript and Research
Resource Identifier (RRID).

+ Yatsenko D, Nguyen T, Shen S, Gunalan K, Turner CA, Guzman R, Sasaki M, Sitonic D,
  Reimer J, Walker EY, Tolias AS. DataJoint Elements: Data Workflows for
  Neurophysiology. bioRxiv. 2021 Jan 1. doi: https://doi.org/10.1101/2021.03.30.437358

+ DataJoint Elements ([RRID:SCR_021894](https://scicrunch.org/resolver/SCR_021894)) -
  Element Calcium Imaging (version `<Enter version number>`)