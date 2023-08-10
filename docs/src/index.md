# Element Calcium Imaging

DataJoint Element for functional calcium imaging with 
[ScanImage](https://docs.scanimage.org/){:target="_blank"}, 
[Scanbox](https://scanbox.org/){:target="_blank"},
[Nikon NIS-Elements](https://www.microscope.healthcare.nikon.com/products/software/nis-elements){:target="_blank"}, 
and `Bruker Prairie View` acquisition software; and 
[Suite2p](https://github.com/MouseLand/suite2p){:target="_blank"}, 
[CaImAn](https://github.com/flatironinstitute/CaImAn){:target="_blank"}, and
[EXTRACT](https://github.com/schnitzer-lab/EXTRACT-public){:target="_blank"} analysis 
software. DataJoint Elements collectively standardize and automate
data collection and analysis for neuroscience experiments. Each Element is a modular
pipeline for data storage and processing with corresponding database tables that can be
combined with other Elements to assemble a fully functional pipeline.

## Experiment Flowchart

![flowchart](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/flowchart.svg)

## Data Pipeline Diagram

![pipeline](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/pipeline_imaging.svg)

+ We have designed three variations of the pipeline to handle different use cases. 
Displayed above is the default `imaging` schema.  Details on all of the `imaging` 
schemas can be found in the [Data Pipeline](./pipeline.md) documentation page.

## Getting Started

+ Please fork the [repository](https://github.com/datajoint/element-calcium-imaging){:target="_blank"}

+ Clone the repository to your computer

  ```bash
  git clone https://github.com/<enter_github_username>/element-calcium-imaging
  ```

+ Install with `pip`

  ```bash
  pip install -e .
  ```

+ [Data Pipeline](./pipeline.md) - Pipeline and table descriptions

+ [Tutorials](./tutorials/index.md) - Start building your data pipeline

+ [Code Repository](https://github.com/datajoint/element-calcium-imaging/){:target="_blank"}

## Support

+ If you need help getting started or run into any errors, please contact our team by 
email at support@datajoint.com.
