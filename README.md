# DataJoint Element - Functional Calcium Imaging
This repository features DataJoint pipeline design for functional Calcium imaging 
with `ScanImage`, `Scanbox`, or `Nikon NIS` acquisition system and `Suite2p` or `CaImAn` suites for analysis. 

The element presented here is not a complete workflow by itself,
 but rather a modular design of tables and dependencies specific to the functional Calcium imaging workflow. 

This modular element can be flexibly attached downstream to 
any particular design of experiment session, thus assembling 
a fully functional calcium imaging workflow.

See [Background](Background.md) for the background information and development timeline.

## Element architecture

![element-calcium-imaging diagram](images/attached_calcium_imaging_element.svg)

+ As the diagram depicts, the imaging element starts immediately downstream from `Session`, and also requires some notion of:

     + `Scanner` for equipment/device

     + `Location` as a dependency for `ScanLocation`

### Scan

+ A `Session` (more specifically an experimental session) may have multiple scans, where each scan describes a complete 4D dataset (i.e. 3D volume over time) from one scanning session, typically from the moment of pressing the *start* button to pressing the *stop* button.

+ `Scan` - table containing information about the equipment used (e.g. the Scanner information)

+ `ScanInfo` - meta information about this scan, from ScanImage header (e.g. frame rate, number of channels, scanning depths, frames, etc.)

+ `ScanInfo.Field` - a field is a 2D image at a particular xy-coordinate and plane (scanning depth) within the field-of-view (FOV) of the scan.

     + For resonant scanner, a field is usually the 2D image occupying the entire FOV from a certain plane (at some depth).

     + For mesoscope scanner, with much wider FOV, there may be multiple fields on one plane. 

### Preprocessing - Motion Correction

+ `MotionCorrection` - motion correction information performed on a scan

+ `MotionCorrection.RigidMotionCorrection` - details of the rigid motion correction (e.g. shifting in x, y) at a per `ScanInfo.Field` level

+ `MotionCorrection.NonRigidMotionCorrection` and `MotionCorrection.Block` tables are used to describe the non-rigid motion correction performed on each `ScanInfo.Field`

+ `MotionCorrection.Summary` - summary images for each `ScanInfo.Field` after motion correction (e.g. average image, correlation image)
    
### Preprocessing - Segmentation

+ `Segmentation` - table specifies the segmentation step and its outputs, following the motion correction step.
 
+ `Segmentation.Mask` - image mask for the segmented region of interest from a particular `ScanInfo.Field`

+ `MaskClassification` - classification of `Segmentation.Mask` into different type (e.g. soma, axon, dendrite, artifact, etc.)

### Neural activity extraction

+ `Fluorescence` - fluorescence traces extracted from each `Segmentation.Mask`

+ `ActivityExtractionMethod` - activity extraction method (e.g. deconvolution) to be applied on fluorescence trace

+ `Activity` - computed neuronal activity trace from fluorescence trace (e.g. spikes)

## Installation

+ Install `element-calcium-imaging`
     ```
     pip install element-calcium-imaging
     ```

+ Upgrade `element-calcium-imaging` previously installed with `pip`
     ```
     pip install --upgrade element-calcium-imaging
     ```

+ Install `element-interface`

     + `element-interface` contains data loading utilities for `element-calcium-imaging`.

     + `element-interface` is a dependency of `element-calcium-imaging`, however it is not contained within `requirements.txt`, therefore, must be installed in addition to the installation of the `element-calcium-imaging`. 

     + `element-interface` can also be used to install packages used for reading acquired data (e.g. `scanreader`) and running analysis (e.g. `CaImAn`).

     + If your workflow uses these packages, you should install them when you install `element-interface`.

     + Install `element-interface` with `scanreader`
          ```
          pip install "element-interface[scanreader] @ git+https://github.com/datajoint/element-interface"
          ```

     + Install `element-interface` with `sbxreader`
          ```
          pip install "element-interface[sbxreader] @ git+https://github.com/datajoint/element-interface"
          ```

     + Install `element-interface` with `Suite2p`
          ```
          pip install "element-interface[suite2p] @ git+https://github.com/datajoint/element-interface"
          ```

     + Install `element-interface` with `CaImAn` requires two separate commands
          ```
          pip install "element-interface[caiman_requirements] @ git+https://github.com/datajoint/element-interface"
          pip install "element-interface[caiman] @ git+https://github.com/datajoint/element-interface"
          ```

     + Install `element-interface` with multiple packages
          ```
          pip install "element-interface[caiman_requirements] @ git+https://github.com/datajoint/element-interface"
          pip install "element-interface[scanreader,sbxreader,suite2p,caiman] @ git+https://github.com/datajoint/element-interface"
          ```

## Element usage

+ See [workflow-calcium-imaging](https://github.com/datajoint/workflow-calcium-imaging) 
repository for an example usage of `element-calcium-imaging`.


    
