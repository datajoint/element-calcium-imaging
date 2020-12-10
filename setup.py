#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys

here = path.abspath(path.dirname(__file__))

long_description = """"
# Pipeline for calcium imaging using ScanImage acquisition software and Suite2p or CaImAn for analysis

Build a full imaging pipeline using the canonical pipeline modules
+ [lab-management](https://github.com/vathes/canonical-lab-management)
+ [colony-management](https://github.com/vathes/canonical-colony-management)
+ [imaging](https://github.com/vathes/canonical-imaging)
"""

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='canonical-full-imaging-pipeline',
    version='0.0.1',
    description="Calcium Imaging pipeline using the DataJoint canonical pipeline modules",
    long_description=long_description,
    author='DataJoint NEURO',
    author_email='info@vathes.com',
    license='MIT',
    url='https://github.com/vathes/canonical-full-imaging-pipeline',
    keywords='neuroscience datajoint calcium-imaging',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=requirements,
)
