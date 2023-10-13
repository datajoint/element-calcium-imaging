# Changelog

Observes [Semantic Versioning](https://semver.org/spec/v2.0.0.html) standard and
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) convention.

## [0.9.0] - 2023-10-13

+ Add - Export to NWB and upload to DANDI

## [0.8.1] - 2023-08-31

+ Fix - Rename `get_image_files` to `get_calcium_imaging_files` where missed

## [0.8.0] - 2023-08-08

+ Update - Rename `get_image_files` to `get_calcium_imaging_files`, and update arguments
+ Update - Remove CaImAn installation from the Dev Container due to memory limits of a free GitHub Codespace account
+ Update - Installation instructions

## [0.7.9] - 2023-07-27

+ Update - GitHub Actions to run every Monday at 8am
+ Update - Dev Container to install CaImAn and rename Docker image
+ Update - `extras_require` to increment `element-interface` version
+ Update - `extras_require` to include `caiman`, `sbxreader`, and `scanreader`

## [0.7.8] - 2023-07-27

+ Update - import statement for `prairie_view_loader` in `scan.py`

## [0.7.7] - 2023-07-13

+ Add - Environment variables for the Python version in the Dev Container
+ Add - Versions for the VS Code extensions in the Dev Container

## [0.7.6] - 2023-06-30

+ Add - Null value for `package_version` in `imaging*` modules to patch bug
+ Update - `tutorial.ipynb` notebook to insert values for nullable attributes

## [0.7.5] - 2023-06-20

+ Update - Requirements

## [0.7.4] - 2023-06-19

+ Add - Dev Container Docker image ID
+ Update - Remove `.devcontainer/local/`
+ Update - Move `docker compose up` command from `devcontainer.json` to README

## [0.7.3] - 2023-06-09

+ Fix - Output of cells within the `tutorial` notebook

## [0.7.2] - 2023-06-08

+ Update - `tutorial` notebook

## [0.7.1] - 2023-06-07

+ Fix - Docs to render notebooks
+ Fix - `get_imaging_root_data_dir` function

## [0.7.0] - 2023-06-06

+ Update - Merge `workflow-calcium-imaging` into `element-calcium-imaging` PR [#135](https://github.com/datajoint/element-calcium-imaging/pull/135)
+ Add - `extras_require` feature to `setup.py`
+ Add - GitHub Actions that call reusable workflows in the `datajoint/.github` repository
+ Update - Replace `get_nd2_files`, etc. functions with `get_image_files` function
+ Add - `tutorial_pipeline.py` script for notebooks to import and activate schemas
+ Update - Replace `reference.Equipment` with `lab.Device` table
+ Update - Remove `demo_prepare.ipynb`
+ Update - Rename `demo_run.ipynb` to `demo.ipynb`
+ Update - `__init__.py` to use environment variables (if available) in place of `dj.config['custom']` values

## [0.6.2] - 2023-05-22

+ Add - CaImAn, Suite2p, and EXTRACT citations

## [0.6.1] - 2023-05-15

+ Update - Docs

## [0.6.0] - 2023-05-15

+ Add - Quality metrics
+ Update - Docs and readme

## [0.5.7] - 2023-05-11

+ Fix - `.ipynb` dark mode output for all notebooks.
+ Fix - Remove `GOOGLE_ANALYTICS_KEY` from `u24_element_release_call.yml`.

## [0.5.6] - 2023-04-28

+ Fix - `.ipynb` output in tutorials is not visible in dark mode.
+ Fix - typos in docstrings.

## [0.5.5] - 2023-04-06

+ Update - Bump `element-interface` requirement to `0.5.1`.

## [0.5.4] - 2023-03-08

+ Add - Requirement for `ipywidgets`
+ Update - Docker Compose file for docs release

## [0.5.3] - 2023-02-23

+ Add - spelling, markdown, and pre-commit config files
+ Add - Notebook rendering to docs

## [0.5.2] - 2023-01-11

+ Bugfix - fix errors in ingesting single-plane PrairieView scans into `ScanInfo`
+ Add - Optional installation of caiman and suite2p through pip

## [0.5.1] - 2022-12-15

+ Add - Imports for prairieview loader

## [0.5.0] - 2022-12-14

+ Add - Cell extraction with EXTRACT package

## [0.4.2] - 2022-11-02

+ Bugfix - Add plotting package to the requirements to generate the figures
+ Add - Scan date parser from nd2 files

## [0.4.1] - 2022-10-28

+ Update - Bump version to trigger PyPI release to revert updates from incorrect tag

## [0.4.0] - 2022-10-28

+ Add - New schema `imaging_report` to compute and store figures from results
+ Add - Widget to display figures

## [0.3.0] - 2022-10-07

+ Add - Reader for `Bruker PrairieView` acquisition system

## [0.2.2] - 2022-09-28

+ Update - Minor table explanation edits
+ Update - Query simplifications
+ Update - Minor code refactoring

## [0.2.1] - 2022-09-12

+ Bugfix - fix errors in auto generating new ProcessingTask

## [0.2.0] - 2022-07-01

+ Add - Imaging module (imaging_preprocess.py) for pre-processing steps

## [0.1.0] - 2022-06-29

+ Add - Support for element-interface
+ Add - Trigger Suite2p and CaImAn
+ Add - Imaging module for no curation
+ Add - Support for Nikon acquisition system
+ Add - `scan_datetime` and `scan_duration` attributes
+ Add - Estimate for scan duration
+ Add - Citation section to README
+ Update - Move background file to elements.datajoint.org
+ Add - Adopt black formatting into code base

## [0.1.0b0] - 2021-05-07

+ Update - First beta release

## [0.1.0a4] - 2021-05-07

+ Update - Add workaround to handle DataJoint 0.13.* [issue #914](https://github.com/datajoint/datajoint-python/issues/914)

## 0.1.0a3 - 2021-05-03

+ Add - GitHub Action release process
+ Add - `scan` and `imaging` modules
+ Add - Readers for `ScanImage`, `ScanBox`, `Suite2p`, `CaImAn`

[0.8.1]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.8.1
[0.8.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.8.0
[0.7.9]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.9
[0.7.8]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.8
[0.7.7]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.7
[0.7.6]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.6
[0.7.5]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.5
[0.7.4]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.4
[0.7.3]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.3
[0.7.2]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.2
[0.7.1]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.1
[0.7.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.7.0
[0.6.2]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.6.2
[0.6.1]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.6.1
[0.6.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.6.0
[0.5.7]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.7
[0.5.6]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.6
[0.5.5]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.5
[0.5.4]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.4
[0.5.3]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.3
[0.5.2]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.2
[0.5.1]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.1
[0.5.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.5.0
[0.4.2]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.4.2
[0.4.1]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.4.1
[0.4.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.4.0
[0.3.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.3.0
[0.2.2]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.2.2
[0.2.1]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.2.1
[0.2.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.2.0
[0.1.0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.1.0
[0.1.0b0]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.1.0b0
[0.1.0a4]: https://github.com/datajoint/element-calcium-imaging/releases/tag/0.1.0a4
