# Data Pipeline

Each node in the following diagram represents the analysis code in the pipeline and the
corresponding table in the database.  Within the pipeline, Element Calcium Imaging
connects to upstream Elements including Lab, Animal, Session, and Event. For more 
detailed documentation on each table, see the API docs for the respective schemas.

The Element is composed of two main schemas, `scan` and `imaging`. To handle
several use cases of this pipeline, we have designed two alternatives to the `imaging` 
schema, including `imaging_no_curation` and `imaging_preprocess`.

## Diagrams

### `imaging` module

- Multiple scans are acquired during each session and each scan is processed independently.

     ![pipeline](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/pipeline_imaging.svg)

### `imaging_no_curation` module

- Same as the `imaging` module, but without the `Curation` table.

     ![pipeline](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/pipeline_imaging_no_curation.svg)

### `imaging_preprocess` module

- Same as the `imaging` module, and additional pre-processing steps can be performed on each scan prior to processing with Suite2p or CaImAn.

     ![pipeline](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/pipeline_imaging_preprocess.svg)

### `multi-scan-processing` branch

- The processing pipeline is typically performed on a per-scan basis, however, depending on the nature of the research questions, different labs may opt to perform processing/segmentation on a concatenated set of data from multiple scans. To this end, we have extended the Calcium Imaging Element and provided a design version capable of supporting a multi-scan processing scheme.

## Table descriptions

### `lab` schema

- For further details see the [lab schema API docs](https://datajoint.com/docs/elements/element-lab/latest/api/element_lab/lab/)

| Table | Description |
| --- | --- |
| Device | Scanner metadata |

### `subject` schema

- Although not required, most choose to connect the `Session` table to a `Subject` table.

- For further details see the [subject schema API docs](https://datajoint.com/docs/elements/element-animal/latest/api/element_animal/subject/)

| Table | Description |
| --- | --- |
| Subject | Basic information of the research subject |

### `session` schema

- For further details see the [session schema API docs](https://datajoint.com/docs/elements/element-session/latest/api/element_session/session_with_datetime/)

| Table | Description |
| --- | --- |
| Session | Unique experimental session identifier |

### `scan` schema

- For further details see the [scan schema API docs](https://datajoint.com/docs/elements/element-calcium-imaging/latest/api/element_calcium_imaging/scan/)

| Table | Description |
| --- | --- |
| AcquisitionSoftware | Software used in the acquisition of the imaging scans |
| Channel | Recording Channel |
| Scan | A set of imaging scans performed in a single session |
| ScanLocation | Anatomical location of the region scanned |
| ScanInfo | Metadata of the imaging scan |
| ScanInfo.Field | Metadata of the fields imaged |
| ScanInfo.ScanFile | Path of the scan file |
| ScanQualityMetrics | Metrics to assess the quality of the scan |
| ScanQualityMetrics.Frames | Metrics used to evaluate each frame |

### `imaging` schema

- For further details see the [imaging schema API docs](https://datajoint.com/docs/elements/element-calcium-imaging/latest/api/element_calcium_imaging/imaging/)

| Table | Description |
| --- | --- |
| ProcessingMethod | Available analysis suites that can be used in processing of the imaging scans |
| ProcessingParamSet | All parameters required to process a calcium imaging scan |
| CellCompartment | Cell compartments that can be imaged |
| MaskType | Available labels for segmented masks |
| ProcessingTask | Task defined by a combination of Scan and ProcessingParamSet |
| Processing | The core table that executes a ProcessingTask |
| Curation | Curated results |
| MotionCorrection | Results of the motion correction procedure |
| MotionCorrection.RigidMotionCorrection | Details of the rigid motion correction performed on the imaging data |
| MotionCorrection.NonRigidMotionCorrection | Details of nonrigid motion correction performed on the imaging data |
| MotionCorrection.NonRigidMotionCorrection.Block | Results of non-rigid motion correction for each block |
| MotionCorrection.Summary | Summary images for each field and channel after motion corrections |
| Segmentation | Results of the segmentation |
| Segmentation.Mask | Masks identified in the segmentation procedure |
| MaskClassificationMethod | Method used in the mask classification procedure |
| MaskClassification | Result of the mask classification procedure |
| MaskClassification.MaskType | Type assigned to each mask |
| Fluorescence | Fluorescence measurements |
| Fluorescence.Trace | Fluorescence traces for each region of interest |
| ActivityExtractionMethod | Method used in activity extraction |
| Activity | Inferred neural activity |
| Activity.Trace | Inferred neural activity from fluorescence traces |
| ProcessingQualityMetrics | Quality metrics used to evaluate the results of the calcium imaging analysis pipeline |
| ProcessingQualityMetrics.Mask | Quality metrics used to evaluate the masks |
| ProcessingQualityMetrics.Trace | Quality metrics used to evaluate the fluorescence traces |
