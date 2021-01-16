# Workflow for calcium imaging data acquired with ScanImage software and analyzed with Suite2p or CaImAn

A complete imaging workflow can be built using the DataJoint elements:
+ [elements-lab](https://github.com/datajoint/elements-lab)
+ [elements-animal](https://github.com/datajoint/elements-animal)
+ [elements-imaging](https://github.com/datajoint/elements-imaging)

This repository provides demonstrations for:
1. Set up a workflow using different elements (see [workflow_imaging/pipeline.py](workflow_imaging/pipeline.py))
2. Ingestion of data/metadata based on:
    + predefined file/folder structure and naming convention
    + predefined directory lookup methods (see [workflow_imaging/paths.py](workflow_imaging/paths.py))
3. Ingestion of clustering results (built-in routine from the imaging pipeline module)


## Workflow architecture

The Calcium imaging workflow presented here uses components from 3 DataJoint elements,
`elements-lab`, `elements-animal` and `elements-imaging`, assembled together to form a fully functional workflow.

### elements-lab

![elements-lab](images/elements_lab_diagram.svg)

### elements-animal

![elements-animal](images/elements_subject_diagram.svg)

### elements-imaging

![elements_imaging](images/elements_imaging_diagram.svg)

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
+ Change directory to `workflow-imaging`
    ```
    cd workflow-imaging
    ```

### Step 2 - Setup a virtual environment

+ It is highly recommended (though not strictly required) to create a virtual environment to run the pipeline.

+ If you are planning on running CaImAn from within this pipeline, you can install this pipeline within the `conda` environment created for the CaImAn installation.
    + [CaImAn installation instructions](https://caiman.readthedocs.io/en/master/Installation.html)

+ You can install with `virtualenv` or `conda`.  Below are the commands for `virtualenv`.

+ If `virtualenv` not yet installed, run `pip install --user virtualenv`

+ To create a new virtual environment named `venv`:
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

### Step 4 - Configure the `dj_local_conf.json`

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

+ Specify database's `hostname`, `username`, and `password` properly.

+ Specify a `database.prefix` to create the schemas.

+ Setup your data directory (`imaging_root_data_dir`) following the convention described below.

### Step 5 (optional) - Jupyter Notebook

+ If you install this repository in a virtual environment, and would like to use it with Jupyter Notebook, follow the steps below:

+ Create a kernel for the virtual environment
    ```
    pip install ipykernel

    ipython kernel install --name=workflow-imaging
    ```

### Installation complete

+ At this point the setup of this workflow is completed.

## Directory structure and file naming convention

+ The workflow presented here is designed to work with the directory structure and file naming convention as described below.

+ The `imaging_root_data_dir` directory is configurable in the `dj_local_conf.json`, under the `custom/imaging_root_data_dir` variable

+ The `subject` directory names must match the identifiers of your subjects in [workflow_imaging/prepare.py](https://github.com/datajoint/workflow-imaging/blob/main/workflow_imaging/prepare.py#L8)

+ The `session` directories must be named with the datetime `yyyymmdd_HHMMSS` of the session
    
+ Each `session` directory should contain:
 
    + All `.tif` files for the scan, with any naming convention
    
    + One `suite2p` subfolder per `session` folder, containing the `Suite2p` analysis outputs

    + One `caiman` subfolder per `session` folder, containing the `CaImAn` analysis output `.hdf5` file, with any naming convention

```
imaging_root_data_dir/
└───<subject1>/                     # Subject name in database
│   └───<session0>/                 # Session datetime `yyyymmdd_HHMMSS`
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
│   └───<session1>/                 # Session datetime `yyyymmdd_HHMMSS`
│   │   │   scan_0001.tif
│   │   │   scan_0002.tif
│   │   │   ...
└───<subject2>/                     # Subject name in database
│   │   ...
```

## Running this workflow

+ Once you have your data directory (`imaging_root_data_dir`) configured with the above convention, populating the workflow with your data amounts to these 3 steps:

1. Insert meta information (e.g. subject, equipment, Suite2p analysis parameters etc.) - modify and run:
    ```
    python workflow_imaging/prepare.py
    ```
2. Import session data - run:
    ```
    python workflow_imaging/ingest.py
    ```
3. Import clustering data and populate downstream analyses - run:
    ```
    python workflow_imaging/populate.py
    ```

+ For inserting new subjects or new analysis parameters, step 1 needs to be re-executed.  Make sure to modify `prepare.py` with the new information.

+ Rerun step 2 and 3 every time new sessions or clustering data become available.

+ In fact, step 2 and 3 can be executed as scheduled jobs that will automatically process any data newly placed into the `imaging_root_data_dir`.

## Interacting with database and exploring data

+ Connect to database and import tables
    ```
    from workflow_imaging.pipeline import *
    ```

+ Query ingested data
    ```
    subject.Subject()
    Session()
    scan.Scan()
    scan.ScanInfo()
    imaging.ProcessingParamSet()
    imaging.ProcessingTask()
    ```

+ If required drop all schemas, the following is the dependency order. 
    ```
    imaging.schema.drop()
    scan.schema.drop()
    schema.drop()
    lab.schema.drop()
    subject.schema.drop()
    ```

+ For a more in-depth exploration of ingested data, please refer to the following example jupyter notebook.
    ```
    jupyter notebook
    /notebooks/explore_data.ipynb
    ```