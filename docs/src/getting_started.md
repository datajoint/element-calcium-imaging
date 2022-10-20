# Installation

## Connecting to a Database

Every DataJoint pipeline needs a relational database to store the data. The 
[general installation instructions](https://elements.datajoint.org/usage/install) 
discuss each of the options for connecting to a database. 

Then, within Python, you can configure DataJoint to use this database.
```python
import datajoint as dj
dj.config['database.host'] = '{YOUR_HOST}'
dj.config['database.user'] = '{YOUR_USERNAME}'
dj.config['database.password'] = '{YOUR_PASS}'
dj.config['custom'] = {'database.prefix': 'your_prefix_'}
dj.config.save_local()
```

## Elements Ecosystem

To use Element Calcium Imaging in conjunction with the other available Elements (including Lab, Animal, and Session), simply download and install 
[Workflow Calcium Imaging](https://github.com/datajoint/workflow-calcium-imaging). We recommend 
doing so in a 
[virtual environment](https://elements.datajoint.org/usage/install/#install-a-virtual-environment) 
(e.g., with Conda).

```bash
git clone https://github.com/datajoint/workflow-calcium-imaging
pip install -e ./workflow-calcium-imaging
```

Then, set the imaging root directory for the Calcium Imaging Workflow.

```python
import datajoint as dj
dj.config['custom'] = {'imaging_root_data_dir' : ['/local/root/', '/data/dirs/']}
dj.config.save_local()
```

You can then activate all the tables with the following command

```python
from workflow_calcium_imaging.pipeline import imaging, scan
```

## Element Alone

To use Element Calcium Imaging without the other Elements, you'll need to install the Element itself. We recommend doing so in a 
[virtual environment](https://elements.datajoint.org/usage/install/#install-a-virtual-environment) 
(e.g., with Conda).

```bash
pip install element-calcium-imaging
```

Then you'll need to supply a couple of tables and functions that the Element relies on. These include...

- Tables:

    - `Session`: A parent table to Scan, identifying a scanning session. 
    [Example](https://github.com/datajoint/element-session/blob/main/element_session/session_with_datetime.py#L45-L50)

    - `Equipment`: A parent table to Scan, identifying a scanning equipment. 
    [Example](https://github.com/datajoint/workflow-calcium-imaging/blob/main/workflow_calcium_imaging/pipeline.py#L42-L53).

- Functions:

    - `get_imaging_root_data_dir()`: Returns absolute path for root data director(y/ies) 
    with all calcium imaging scans, as (list of) string(s). 
    [Example](https://github.com/datajoint/workflow-calcium-imaging/blob/main/workflow_calcium_imaging/paths.py#L5-L12).

    - `get_imaging_processed_data_dir()`: Optional. Returns absolute path for processed 
    data. Defaults to session video subfolder. 
    [Example](https://github.com/datajoint/workflow-calcium-imaging/blob/main/workflow_calcium_imaging/paths.py#L15-L23)

Each of these items should be present in the namespace of a single script (e.g., 
[a pipeline script](https://github.com/datajoint/workflow-calcium-imaging/blob/main/workflow_calcium_imaging/pipeline.py)). 
This script should also activate each schema from the Element you plan to use (e.g., 
[activation command](https://github.com/datajoint/workflow-calcium-imaging/blob/main/workflow_calcium_imaging/pipeline.py#L59-L60)). 
The required items above are passed to the Element via `linking_module`.