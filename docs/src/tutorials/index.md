# Tutorials

+ Element Calcium Imaging includes an [interactive tutorial on GitHub Codespaces](https://github.com/datajoint/element-calcium-imaging#interactive-tutorial), which is configured for users to run the pipeline.

+ DataJoint Elements are modular and can be connected into a complete pipeline.  In the interactive tutorial are example Jupyter notebooks that combine five DataJoint Elements - Lab, Animal, Session, Event, and Calcium Imaging.  The notebooks describe the pipeline and provide instructions for running the pipeline.  For convenience, these notebooks are also rendered on this website:
   + [Tutorial notebook](tutorial.ipynb)
   + [Quality metrics notebook](quality_metrics.ipynb)

## Installation Instructions for Active Projects

+ The Element Calcium Imaging described above can be modified for a user's specific experimental requirements and thereby used in active projects.  

+ The GitHub Codespace and Dev Container is configured for tutorials and prototyping.  
We recommend users to configure a database specifically for production pipelines.  Instructions for a local installation of the integrated development environment with a database can be found on the [User Guide](https://datajoint.com/docs/elements/user-guide/) page.

## Videos

[![YouTube tutorial](https://img.youtube.com/vi/gFLn0GB1L30/0.jpg)](https://www.youtube.com/watch?v=gFLn0GB1L30)

+ The [YouTube tutorial](https://www.youtube.com/watch?v=gFLn0GB1L30) gives an overview 
of the workflow files and notebooks, as well as core concepts related to calcium imaging
analysis.

## EXTRACT

+ Analysis with the EXTRACT package is currently supported for single channel, single
plane scans using Suite2p for motion correction. For processing with EXTRACT,
please set `processing_method="extract"` in the
ProcessingParamSet table, and provide the `params` attribute of the ProcessingParamSet
table in the `{'suite2p': {...}, 'extract': {...}}` dictionary format. Please also
install the [MATLAB engine](https://pypi.org/project/matlabengine/) API for Python.

## Manual ROI Mask Creation and Curation

+ Manual creation of ROI masks for fluorescence activity extraction is supported by the `draw_rois.py` plotly/dash widget. This widget allows the user to draw new ROI masks and submit them to the database. The widget can be launched in a Jupyter notebook after following the [installation instructions](#installation-instructions-for-active-projects) and importing `draw_rois` from the module.
+ ROI masks can be curated using the `widget.py` jupyter widget that allows the user to mark each regions as either a `cell` or `non-cell`. This widget can be launched in a Jupyter notebook after following the [installation instructions](#installation-instructions-for-active-projects) and importing `main` from the module.
