# Element Calcium Imaging

Element Calcium Imaging is a DataJoint pipeline that standardizes and automates
data collection and analysis for calcium imaging experiments. It supports the most popular
acquisition systems `ScanImage`, `Scanbox`, and `Nikon NIS` and operates the leading analysis
suites `Suite2p` and `CaImAn` seamlessly.

Element Calcium Imaging is a modular pipeline that can be combined with other Elements to
assemble a fully functional pipeline and/or construct multimodal pipelines.

The element itself is comprised of two schemas, `scan` and `imaging`.  To handle
several use cases of this pipeline, we have designed two alternatives to `imaging` schemas,
including `imaging_no_curation` and `imaging_preprocess`. Visit the [concepts page](./concepts.md)
for more information on the Element Calcium Imaging. To get started with building your data pipeline
navigate to the [Tutorials](./tutorials.md) page.

![element-calcium-imaging diagram](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/attached_calcium_imaging_element.svg)