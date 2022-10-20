# Concepts

## Description of modality, user population
Over the past two decades, in vivo two-photon laser-scanning imaging of calcium signals has evolved into a mainstream modality for neurophysiology experiments to record population activity in intact neural circuits. The tools for signal acquisition and analysis continue to evolve but common patterns and elements of standardization have emerged.

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

## Preprocessing toolchain: development teams
The preprocessing workflow for two-photon laser-scanning microscopy includes motion correction (rigid or non-rigid), cell segmentation, and calcium event extraction (sometimes described as "deconvolution" or "spike inference"). Some include raster artifact correction, cropping and stitching operations.

Until recently, most labs have developed custom processing pipelines, sharing them with others as academic open-source projects. Recently, a few leaders have emerged as standardization candidates for the initial preprocessing.

- [CaImAn](https://github.com/flatironinstitute/CaImAn) (Originally developed by Andrea Giovannucci, current support by FlatIron Institute: Eftychios A. Pnevmatikakis, Johannes Friedrich)
- [Suite2p](https://github.com/MouseLand/suite2p) (Carsen Stringer and Marius Pachitariu at Janelia), 200+ users, active support

## Key projects
Over the past few years, several labs have developed DataJoint-based data management and processing pipelines for two-photon Calcium imaging. Our team collaborated with several of them during their projects. Additionally, we interviewed these teams to understand their experiment workflow, pipeline design, associated tools, and interfaces.

These teams include: + MICrONS (Andreas Tolias Lab, BCM) - https://github.com/cajal + BrainCoGs (Princeton) - https://github.com/BrainCOGS + Moser Group (Kavli Institute/NTNU) - private repository + Anne Churchland Lab (UCLA)

## Pipeline Development
Through our interviews and direct collaboration on the precursor projects, we identified the common motifs to create the Calcium Imaging Element with the repository hosted at https://github.com/datajoint/element-calcium-imaging.

Major features of the Calcium Imaging Element include: + Pipeline architecture defining: + Calcium-imaging scanning metadata, also compatible with mesoscale imaging and multi-ROI scanning mode + Tables for all processing steps: motion correction, segmentation, cell spatial footprint, fluorescence trace extraction, spike inference and cell classification + Store/track/manage different curations of the segmentation results + Ingestion support for data acquired with ScanImage and Scanbox acquisition systems + Ingestion support for processing outputs from both Suite2p and CaImAn analysis suites + Sample data and complete test suite for quality assurance

The processing workflow is typically performed on a per-scan basis, however, depending on the nature of the research questions, different labs may opt to perform processing/segmentation on a concatenated set of data from multiple scans. To this end, we have extended the Calcium Imaging Element and provided a design version capable of supporting a multi-scan processing scheme.
