#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys

pkg_name = 'workflow_calcium_imaging'
here = path.abspath(path.dirname(__file__))

long_description = """"
# Workflow for calcium imaging data acquired with ScanImage software and analyzed with Suite2p or CaImAn.

Build a complete imaging workflow using the DataJoint elements
+ [elements-lab](https://github.com/datajoint/elements-lab)
+ [elements-animal](https://github.com/datajoint/elements-animal)
+ [elements-imaging](https://github.com/datajoint/elements-imaging)
"""

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

with open(path.join(here, pkg_name, 'version.py')) as f:
    exec(f.read())

setup(
    name='workflow-imaging',
    version=__version__,
    description="Calcium imaging workflow using the DataJoint elements",
    long_description=long_description,
    author='DataJoint NEURO',
    author_email='info@vathes.com',
    license='MIT',
    url='https://github.com/datajoint/workflow-imaging',
    keywords='neuroscience datajoint calcium-imaging',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=requirements,
)
