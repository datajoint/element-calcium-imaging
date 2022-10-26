# Concepts

## Description of modality, user population
Over the past two decades, in vivo two-photon laser-scanning imaging of calcium signals has evolved into a mainstream modality for neurophysiology experiments to record population activity in intact neural circuits. The tools for signal acquisition and analysis continue to evolve but common patterns and elements of standardization have emerged.

## Preprocessing toolchain: development teams
The preprocessing workflow for two-photon laser-scanning microscopy includes motion correction (rigid or non-rigid), cell segmentation, and calcium event extraction (sometimes described as "deconvolution" or "spike inference"). Some include raster artifact correction, cropping and stitching operations.


![Raw Scans](/images/rawscans.gif){: style="height:250px"}
![Motion Corrected Scans](/images/motioncorrectedscans.gif){: style="height:250px"}
![Cell Segmentation](/images/cellsegmentation.png){: style="height:250px"}
![Calcium Events](/images/calciumtraces.png){: style="height:250px"}

For a long time, most labs developed custom processing pipelines, sharing them with others as academic open-source projects. This has changed recently with the emerging of a few leaders as the standardization candidates for the initial preprocessing.

- [CaImAn](https://github.com/flatironinstitute/CaImAn) (Originally developed by Andrea Giovannucci, current support by FlatIron Institute: Eftychios A. Pnevmatikakis, Johannes Friedrich)
- [Suite2p](https://github.com/MouseLand/suite2p) (Carsen Stringer and Marius Pachitariu at Janelia), 200+ users, active support

Element Calcium Imaging encapsulates these packages to ease the management of data and its analysis.

## Element Architecture
Each node in the following diagram represents the analysis code in the workflow and the corresponding table in the database.  Within the workflow, Element Calcium Imaging connects to upstream Elements including Lab, Animal, and Session. For more detailed documentation on each table, see the API docs for the respective schemas.

![element-calcium-imaging diagram](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/attached_calcium_imaging_element.svg)

### `lab` schema ([API docs](../api/workflow_calcium_imaging/pipeline/#workflow_calcium_imaging.pipeline.Equipment))

| Table | Description |
| --- | --- |
| Equipment | Scanner metadata |

### `subject` schema ([API docs](https://datajoint.com/docs/elements/element-animal/api/element_animal/subject))
- Although not required, most choose to connect the `Session` table to a `Subject` table.

| Table | Description |
| --- | --- |
| Subject | Basic information of the research subject |

### `session` schema ([API docs](https://datajoint.com/docs/elements/element-session/api/element_session/session_with_datetime))

| Table | Description |
| --- | --- |
| Session | Unique experimental session identifier |


### `scan` schema ([API docs](https://datajoint.com/docs/elements/element-calcium-imaging/api/element_calcium_imaging/scan))

| Table | Description |
| --- | --- |
| AcquisitionSoftware | Software used in the acquisiton of the imaging scans |
| Channel | Recording Channel |
| Scan | A set of imaging scans perfomed in a single session |
| ScanLocation | Anatomical location of the region scanned |
| ScanInfo | Metadata of the imaging scan |
| ScanInfo.Field | Metadata of the fields imaged |
| ScanInfo.ScanFile | Path of the scan file |

### `imaging` schema ([API docs](https://datajoint.com/docs/elements/element-calcium-imaging/api/element_calcium_imaging/imaging))

| Table | Description |
| --- | --- |
| ProcessingMethod | Available analysis suites that can be used in processing of the imaging scans |
| ProcessingParamSet | All parameters required to process a calcium imaging scan |
| CellCompartment | ?? |
| MaskType ||
| ProcessingTask | Task defined by a combination of Scan and ProcessingParamSet |
| Processing | The core table that executes a ProcessingTask |
| Curation | Curated results |
| MotionCorrection | Results of the motion correction procedure |
| MotionCorrection.RigidMotionCorrection | Results of the rigid motion correction procedure |
| MotionCorrection.NonRigidMotionCorrection | ??? |
| MotionCorrection.NonRigidMotionCorrection.Block | Results of non-rigid motion correction for each block |
| MotionCorrection.Summary | ??? |
| Segmentation | Results of the segmentation |
| Segmentation.Mask | Masks identified in the segmentation procedure |
| MaskClassificationMethod | Method used in the mask classification procedure |
| MaskClassification | Result of the mask classification procedure |
| MaskClassification.MaskType |  |
| Fluorescence | Fluorescence measurements |
| Fluorescence.Trace | Fluorescence traces for each region of interest |
| ActivityExtractionMethod | Method used in activity extraction |
| Activity | Inferred neural activity |
| Activity.Trace | Inferred neural activity from fluorescence traces |


## Acquisition tools

### Hardware
The primary acquisition systems are: + Sutter (we estimate 400 rigs in active use - TBC) + Thorlabs (we estimate 400 rigs in active use - TBC) + Bruker (we estimate 400 rigs in active use - TBC) + Neurolabware (we estimate 400 rigs in active use - TBC)

We do not include Miniscopes in these estimates. In all there are perhaps on the order of 3000 two-photon setups globally but their processing needs may need to be further segmented.

### Software
- ScanImage
- ThorImageLS
- Scanbox
- Nikon

Vidrio’s [ScanImage](https://docs.scanimage.org/) is the data acquisition software for two types of home-built scanning two-photon systems, either based on Thorlabs and Sutter hardware. ScanImage has a free version and a licensed version. Thorlabs also provides their own acquisition software - ThorImageLS (probably half of the systems).


## Key projects
Over the past few years, several labs have developed DataJoint-based data management and processing pipelines for two-photon Calcium imaging. Our team collaborated with several of them during their projects. Additionally, we interviewed these teams to understand their experiment workflow, pipeline design, associated tools, and interfaces.

These teams include: + MICrONS (Andreas Tolias Lab, BCM) - https://github.com/cajal + BrainCoGs (Princeton) - https://github.com/BrainCOGS + Moser Group (Kavli Institute/NTNU) - private repository + Anne Churchland Lab (UCLA)

## Pipeline Development
Through our interviews and direct collaboration on the precursor projects, we identified the common motifs to create the Calcium Imaging Element with the repository hosted at https://github.com/datajoint/element-calcium-imaging.

Major features of the Calcium Imaging Element include: + Pipeline architecture defining: + Calcium-imaging scanning metadata, also compatible with mesoscale imaging and multi-ROI scanning mode + Tables for all processing steps: motion correction, segmentation, cell spatial footprint, fluorescence trace extraction, spike inference and cell classification + Store/track/manage different curations of the segmentation results + Ingestion support for data acquired with ScanImage and Scanbox acquisition systems + Ingestion support for processing outputs from both Suite2p and CaImAn analysis suites + Sample data and complete test suite for quality assurance

The processing workflow is typically performed on a per-scan basis, however, depending on the nature of the research questions, different labs may opt to perform processing/segmentation on a concatenated set of data from multiple scans. To this end, we have extended the Calcium Imaging Element and provided a design version capable of supporting a multi-scan processing scheme.