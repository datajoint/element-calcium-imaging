# DataJoint Workflow - Calcium Imaging
Workflow for calcium imaging data acquired with ScanImage or ScanBox software and analyzed with Suite2p or CaImAn

A complete `workflow-imaging` can be built using the DataJoint elements:
+ [elements-lab](https://github.com/datajoint/elements-lab)
+ [elements-animal](https://github.com/datajoint/elements-animal)
+ [elements-imaging](https://github.com/datajoint/elements-imaging)

This repository provides demonstrations for:
1. Set up a workflow using different elements (see [workflow_imaging/pipeline.py](workflow_imaging/pipeline.py))
2. Ingestion of data/metadata based on:
    + predefined file/folder structure and naming convention
    + predefined directory lookup methods (see [workflow_imaging/paths.py](workflow_imaging/paths.py))
3. Ingestion of clustering results (built-in routine from the imaging element)

+ This workflow provides support for calcium imaging data acquired with the `ScanImage`, `ScanBox`, or `Miniscope-DAQ` systems.  And for data processed with `Suite2p`, `CaImAn`, or `Miniscope Analysis`.
    + Note the [`Miniscope Analysis`](https://github.com/etterguillaume/MiniscopeAnalysis) package is not currently maintained.

## Workflow architecture

The calcium imaging workflow presented here uses components from three DataJoint elements, 
`elements-lab`, `elements-animal` and `elements-imaging`, assembled together to form a fully functional workflow.

### elements-lab

![elements-lab](images/elements_lab_diagram.svg)

### elements-animal

![elements-animal](images/elements_subject_diagram.svg)

### elements-imaging

![elements_imaging](images/elements_imaging_diagram.svg)

## Installation instructions

### Step 1 - Clone this repository

+ It is recommended to fork this repository and install a clone of your fork.

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

From the root of the cloned repository directory:
    ```
    pip install -e .
    ```

Note: the `-e` flag will install this repository in editable mode, 
in case there's a need to modify the code (e.g. the `pipeline.py` or `paths.py` scripts). 
If no such modification required, using `pip install .` is sufficient

### Step 4 - Install `sbxreader` module

+ If you are planning on working with data acquired with the ScanBox system, you will need to install the [sbxreader](https://github.com/jcouto/sbxreader) module.
    ```
    pip install sbxreader
    ```

### Step 5 - Jupyter Notebook
+ Register an IPython kernel with Jupyter
    ```
    ipython kernel install --name=workflow-imaging
    ```

### Step 6 - Configure the `dj_local_conf.json`

At the root of the repository folder, 
create a new file `dj_local_conf.json` with the following template:

```json
{
  "database.host": "<hostname>",
  "database.user": "<username>",
  "database.password": "<password>",
  "loglevel": "INFO",
  "safemode": true,
  "display.limit": 7,
  "display.width": 14,
  "display.show_tuple_count": true,
  "custom": {
      "database.prefix": "<neuro_>",
      "imaging_root_data_dir": "<C:/data/imaging_root_data_dir>"
    }
}
```

+ Specify database's `hostname`, `username`, and `password` properly.

+ Specify a `database.prefix` to create the schemas.

+ Setup your data directory (`imaging_root_data_dir`) following the convention described below.

### Installation complete

+ At this point the setup of this workflow is complete.

## Directory structure and file naming convention

The workflow presented here is designed to work with the directory structure and file naming convention as described below.

Note: the `imaging-element` is designed to accommodate multiple scans per session, 
however, in this particular `workflow-imaging`, we take the assumption that there is only ***one scan per session***.

+ The `imaging_root_data_dir` directory is configurable in the `dj_local_conf.json`, under the `custom/imaging_root_data_dir` variable

+ The `subject` directory names must match the identifiers of your subjects in the [subjects.csv](./user_data/subjects.csv) script

+ The `session` directories can have any naming convention
    
+ Each `session` directory should contain:
 
    + All `.tif` or `.sbx` or `.json` files for the scan, with any naming convention
    
    + One `suite2p` subfolder per `session` folder, containing the `Suite2p` analysis outputs

    + One `caiman` subfolder per `session` folder, containing the `CaImAn` analysis output `.hdf5` file, with any naming convention

    + One `miniscope_analysis` subfolder per `session` folder, containing the `Miniscope Analysis` output `ms.mat` and `SFP.mat` files

```
imaging_root_data_dir/
└───<subject1>/                     # Subject name in `subjects.csv`
│   └───<session0>/                 # Session directory in `sessions.csv`
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
│   └───<session1>/                 # Session directory in `sessions.csv`
│   │   │   scan_0001.tif
│   │   │   scan_0002.tif
│   │   │   ...
└───<subject2>/                     # Subject name in `subjects.csv`
│   │   ...
```

## Running this workflow

See `notebooks/run_workflow.ipynb` for detailed instructions on running this workflow.

Once you have your data directory (`imaging_root_data_dir`) configured with the above convention, 
populating the workflow with your data amounts to these 3 steps:

1. Insert meta information (e.g. subject, sessions, equipment, Suite2p analysis parameters etc.) - modify:
    + user_data/subjects.csv
    + user_data/sessions.csv

2. Import session data - run:
    ```
    python workflow_imaging/ingest.py
    ```
   
3. Import scan data and populate downstream analyses - run:
    ```
    python workflow_imaging/populate.py
    ```

+ For inserting new subjects, sessions or new analysis parameters, step 1 needs to be repeated.

+ Rerun step 2 and 3 every time new sessions or processed data becomes available.

+ In fact, step 2 and 3 can be executed as scheduled jobs that will automatically process any data newly placed into the `imaging_root_data_dir`.

## Interacting with the DataJoint pipeline and exploring data

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

+ If required to drop all schemas, the following is the dependency order. 
    ```
    from workflow_imaging.pipeline import *

    imaging.schema.drop()
    scan.schema.drop()
    schema.drop()
    subject.schema.drop()
    lab.schema.drop()
    ```

+ For a more in-depth exploration of ingested data, please refer to the example [notebook](notebooks/explore_workflow.ipynb).


## Development mode installation

This method allows you to modify the source code for `workflow-imaging`, `elements-imaging`, `elements-animal`, and `elements-lab`.

+ Launch a new terminal and change directory to where you want to clone the repositories
    ```
    cd C:/Projects
    ```
+ Clone the repositories
    ```
    git clone https://github.com/datajoint/elements-lab
    git clone https://github.com/datajoint/elements-animal
    git clone https://github.com/datajoint/elements-imaging
    git clone https://github.com/datajoint/workflow-imaging
    ```
+ Install each package with the `-e` option
    ```
    pip install -e ./workflow-imaging
    pip install -e ./elements-lab
    pip install -e ./elements-animal
    pip install -e ./elements-imaging
    ```