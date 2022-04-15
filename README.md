# DataJoint Workflow - Calcium Imaging

Workflow for calcium imaging data acquired with 
[ScanImage](http://scanimage.vidriotechnologies.com),  
[Scanbox](https://scanbox.org), or `Nikon NIS` software and processed with 
[Suite2p](https://github.com/MouseLand/suite2p) or 
[CaImAn](https://github.com/flatironinstitute/CaImAn).

A complete calcium imaging workflow can be built using the DataJoint Elements.
+ [element-lab](https://github.com/datajoint/element-lab)
+ [element-animal](https://github.com/datajoint/element-animal)
+ [element-session](https://github.com/datajoint/element-session)
+ [element-calcium-imaging](https://github.com/datajoint/element-calcium-imaging)

This repository provides demonstrations for:
1. Set up a workflow using DataJoint Elements (see 
[workflow_calcium_imaging/pipeline.py](workflow_calcium_imaging/pipeline.py))
2. Ingestion of data/metadata based on a predefined file structure, file naming 
convention, and directory lookup methods (see 
[workflow_calcium_imaging/paths.py](workflow_calcium_imaging/paths.py)).
3. Ingestion of segmentation and deconvolution results.

## Workflow architecture

The calcium imaging workflow presented here uses components from four DataJoint 
Elements ([element-lab](https://github.com/datajoint/element-lab), 
[element-animal](https://github.com/datajoint/element-animal), 
[element-session](https://github.com/datajoint/element-session), 
[element-calcium-imaging](https://github.com/datajoint/element-calcium-imaging)) 
assembled together to form a fully functional workflow. 

![element_calcium_imaging](images/attached_calcium_imaging_element.svg)

## Installation instructions

+ The installation instructions can be found at 
[datajoint-elements/install.md](
     https://github.com/datajoint/datajoint-elements/blob/main/gh-pages/docs/usage/install.md).

## Interacting with the DataJoint workflow

+ Please refer to the following workflow-specific 
[Jupyter notebooks](/notebooks) for an in-depth explanation of how to run the 
workflow ([03-process.ipynb](notebooks/03-process.ipynb)) and explore the data 
([05-explore.ipynb](notebooks/05-explore.ipynb)).

## Citation

+ If your work uses DataJoint and DataJoint Elements, please cite the respective Research Resource Identifiers (RRIDs) and manuscripts.

+ DataJoint for Python or MATLAB
    + Yatsenko D, Reimer J, Ecker AS, Walker EY, Sinz F, Berens P, Hoenselaar A, Cotton RJ, Siapas AS, Tolias AS. DataJoint: managing big scientific data using MATLAB or Python. bioRxiv. 2015 Jan 1:031658. doi: https://doi.org/10.1101/031658

    + DataJoint ([RRID:SCR_014543](https://scicrunch.org/resolver/SCR_014543)) - DataJoint for <Python or MATLAB> (version < enter version number >)

+ DataJoint Elements
    + Yatsenko D, Nguyen T, Shen S, Gunalan K, Turner CA, Guzman R, Sasaki M, Sitonic D, Reimer J, Walker EY, Tolias AS. DataJoint Elements: Data Workflows for Neurophysiology. bioRxiv. 2021 Jan 1. doi: https://doi.org/10.1101/2021.03.30.437358

    + DataJoint Elements ([RRID:SCR_021894](https://scicrunch.org/resolver/SCR_021894)) - Element Calcium Imaging (version < enter version number >)