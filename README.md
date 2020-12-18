# Workflow for calcium imaging data acquired with ScanImage software and analyzed with Suite2p or CaImAn

A complete imaging workflow can be built using the DataJoint elements:
+ [elements-lab](https://github.com/datajoint/elements-lab)
+ [elements-animal](https://github.com/datajoint/elements-animal)
+ [elements-imaging](https://github.com/datajoint/elements-imaging)

This repository provides demonstrations for: 
1. Set up a pipeline using different pipeline modules (see [here](workflow_imaging/pipeline.py))
2. Ingestion of data/metadata based on:
    + predefined file/folder structure and naming convention
    + predefined directory lookup methods (see [here](workflow_imaging/paths.py))
3. Ingestion of clustering results (built-in routine from the imaging pipeline module)


## Pipeline Architecture

The Calcium imaging pipeline presented here uses pipeline components from 3 DataJoint pipeline elements, 
***elements-lab***, ***elements-animal*** and ***elements-imaging***, assembled together to form a fully functional pipeline. 

### elements-lab

![elements-lab](images/lab_erd.svg)

### elements-animal

![elements-animal](images/subject_erd.svg)

### assembled with elements-imaging

![assembled_pipeline](images/attached_imaging_erd.svg)

## Installation instructions

### Step 1 - Clone this project

+ Launch a new terminal and change directory to where you want to clone the repository
    ```
    cd C:/Projects
    ```
+ Clone the repository
    ```
    git clone https://github.com/datajoint/workflow-imaging 
    ```
+ Change directory to ***workflow-imaging***
    ```
    cd workflow-imaging
    ```

### Step 2 - Setup a virtual environment

+ It is highly recommended (though not strictly required) to create a virtual environment to run the pipeline.

+ If you are planning on running CaImAn from within this pipeline, you can install this pipeline within the conda environment created for the CaImAn installation.
    + [CaImAn installation instructions](https://caiman.readthedocs.io/en/master/Installation.html)

+ You can install with `virtualenv` or `conda`.  Below are the commands for `virtualenv`.

+ If `virtualenv` not yet installed, run `pip install --user virtualenv`

+ To create a new virtual environment named ***venv***:
    ```
    virtualenv venv
    ```

+ To activated the virtual environment:
    + On Windows:
        ```
        .\venv\Scripts\activate
        ```

    + On Linux/macOS:
        ```
        source venv/bin/activate
        ```

### Step 3 - Install this repository

+ From the root of the cloned repository directory:
    ```
    pip install .
    ```

### Step 4 - Configure the ***dj_local_conf.json***

+ At the root of the repository folder, create a new file `dj_local_conf.json` with the following template:
 
```json
{
  "database.host": "hostname",
  "database.user": "username",
  "database.password": "password",
  "loglevel": "INFO",
  "safemode": true,
  "display.limit": 7,
  "display.width": 14,
  "display.show_tuple_count": true,
  "custom": {
      "database.prefix": "neuro_",
      "imaging_root_data_dir": "C:/data/imaging_root_data_dir"
    }
}
```

+ Specify database's `hostname`, `username` and `password` properly. 

+ Specify a `database.prefix` to create the schemas.

+ Setup your data directory following the convention described below.

### Step 5 (optional) - Jupyter Notebook

+ If you install this repository in a virtual environment, and would like to use it with Jupyter Notebook, follow the steps below:

+ Create a kernel for the virtual environment
    ```
    pip install ipykernel
    
    ipython kernel install --name=workflow-imaging
    ```

+ At this point the setup/installation of this pipeline is completed. Users can start browsing the example jupyter notebooks for demo usage of the pipeline.
    ```
    jupyter notebook
    ```

## Directory structure and file naming convention

+ The pipeline presented here is designed to work with the directory structure and file naming convention as followed

```
root_data_dir/
└───subject1/
│   └───session0/
│   │   │   scan_0001.tif
│   │   │   scan_0002.tif
│   │   │   scan_0003.tif
│   │   │   ...
│   │   └───suite2p/
│   │       │   ops1.npy
│   │       └───plane0/
│   │       │   │   ops.npy
│   │       │   │   spks.npy
│   │       │   │   stat.npy
│   │       │   │   ...
│   │       └───plane1/
│   │           │   ops.npy
│   │           │   spks.npy
│   │           │   stat.npy
│   │           │   ...
│   │   └───caiman/
│   │       │   analysis_results.hdf5
│   └───session1/
│   │   │   scan_0001.tif
│   │   │   scan_0002.tif
│   │   │   ...
└───subject2/
│   │   ...
```

+ ***root_data_dir*** is configurable in the `dj_local_conf.json`,
 under `custom/imaging_data_dir` variable
+ the ***subject*** directories must match the identifier of your subjects
+ the ***session*** directories must match the following naming convention:

    yyyymmdd_HHMMSS (where yyyymmdd_HHMMSS is the datetime of the session)  
    
+ and each containing:
 
    + all *.tif* files for the scan
    
    + one ***suite2p*** subfolder per session folder, containing the ***Suite2p*** analysis outputs

    + one ***caiman*** subfolder per session folder, containing the ***CaImAn*** analysis output (*.hdf5)

## Running this pipeline

+ Once you have your data directory configured with the above convention,
 populating the pipeline with your data amounts to these 3 steps:
 
1. Insert meta information (e.g. subject, equipment, Suite2p analysis parameters etc.) - modify and run:
    ```
    python workflow_imaging/prepare.py
    ```
2. Import session data - run:
    ```
    python workflow_imaging/ingestion.py
    ```
3. Import clustering data and populate downstream analyses - run:
    ```
    python workflow_imaging/populate.py
    ```
    
+ For inserting new subjects or new analysis parameters, step 1 needs to be re-executed (make sure to modify the `prepare.py` with the new information)

+ Rerun step 2 and 3 every time new sessions or clustering data become available.

+ In fact, step 2 and 3 can be executed as scheduled jobs that will automatically process any data newly placed into the ***root_data_dir***