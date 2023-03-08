# DataJoint Workflow - Functional Calcium Imaging

DataJoint Workflow for functional calcium imaging combines multiple DataJoint Elements to process data acquired with [ScanImage](http://scanimage.vidriotechnologies.com), [Scanbox](https://scanbox.org), `Nikon
NIS`, or `PrairieView` acquisition software, using [Suite2p](https://github.com/MouseLand/suite2p) or [CaImAn](https://github.com/flatironinstitute/CaImAn) analysis software. DataJoint Elements collectively standardize and automate data collection and analysis for neuroscience experiments. Each Element is a modular pipeline for data storage and processing with corresponding database tables that can be combined with other Elements to assemble a fully functional pipeline.

To get started, see below for an [interactive tutorial](#interactive-tutorial) on GitHub Codespaces.  More information can be found at the
[Element documentation page](https://datajoint.com/docs/elements/element-calcium-imaging).

![diagram](https://raw.githubusercontent.com/datajoint/element-calcium-imaging/main/images/diagram_flowchart.svg)

## Interactive tutorial

The easiest way to learn about DataJoint Elements is to use the tutorial notebook within a [GitHub Codespace](https://docs.github.com/en/codespaces/overview). Please follow the steps below for the best experience:

1. Fork this repository to your GitHub account.

2. Select the green `Code` button.

3. Within the dropdown menu, select the `Codespaces` tab.

4. Select the green `Create codespace on main` button.

5. The environment is ready when a Visual Studio Code window is rendered within your browser.  This takes ~5 minutes the first time being launched, and ~1 minute if you revisit this Codespace.

6. Navigate to the `notebooks` directory on the left panel and open the `tutorial.ipynb` Jupyter notebook. Execute the cells in this notebook to begin your walk through the tutorial.

7. Once you are done, GitHub will automatically terminate the Codespace after 30 minutes of inactivity or you can manually terminate the Codespace.

+ If you are new to GitHub and run into any errors, please contact us via email at support@datajoint.com. If you are experienced with GitHub, please create an issue on the upstream repository or issue a pull request with a thorough explanantion of the error and proposed solution.

**Please Note:**

+ GitHub Codespaces are limited to 120 core-hours per month for free users. Once you exceed this limit, you will have to wait for the hours to reset or pay to use Codespaces.
