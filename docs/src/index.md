# Element Calcium Imaging

DataJoint element for functional calcium imaging with `ScanImage`, `Scanbox`,
`Nikon NIS`, or `PrairieView` acquisition systems and `Suite2p` or `CaImAn` suites
for analysis. DataJoint Elements collectively standardize and automate data collection
and analysis for neuroscience experiments. Each Element is a modular pipeline for data
storage and processing with corresponding database tables that can be combined with
other Elements to assemble a fully functional pipeline.

The Element is composed of two main schemas, `scan` and `imaging`. To handle
several use cases of this pipeline, we have designed two alternatives to `imaging` schemas,
including `imaging_no_curation` and `imaging_preprocess`.

- `imaging` module - Multiple scans are acquired during each session and each scan is
processed independently.

![element-calcium-imaging diagram](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/attached_calcium_imaging_element.svg)

- `imaging_preprocess` module - Same as `imaging` module. Additionally, pre-processing
steps can be performed on each scan prior to processing with Suite2p or CaImAn.
![element-calcium-imaging diagram](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/attached_calcium_imaging_element_preprocess.svg)

Visit the [concepts page](./concepts.md) for more information on the Element Calcium Imaging.
To get started with building your data pipeline navigate to the [Tutorials](./tutorials.md) page.
