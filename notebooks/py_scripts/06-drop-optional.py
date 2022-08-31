# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: 'Python 3.7.9 64-bit (''workflow-calcium-imaging'': conda)'
#     name: python379jvsc74a57bd01a512f474e195e32ad84236879d3bb44800a92b431919ef0b10d543f5012a23c
# ---

# # Drop schemas
#
# + Schemas are not typically dropped in a production workflow with real data in it. 
# + At the developmental phase, it might be required for the table redesign.
# + When dropping all schemas is needed, the following is the dependency order.

# Change into the parent directory to find the `dj_local_conf.json` file. 

import os
if os.path.basename(os.getcwd()) == "notebooks": os.chdir("..")

from workflow_calcium_imaging.pipeline import *

# +
# imaging.schema.drop()
# scan.schema.drop()
# session.schema.drop()
# subject.schema.drop()
# lab.schema.drop()
# -


