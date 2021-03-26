#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys

pkg_name = 'element_calcium_imaging'
here = path.abspath(path.dirname(__file__))

long_description = """"
DataJoint Element for multi-photon calcium imaging data analyzed with Suite2p and/or CaImAn.
"""

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

with open(path.join(here, pkg_name, 'version.py')) as f:
    exec(f.read())

setup(
    name='element-calcium-imaging',
    version=__version__,
    description="Calcium Imaging DataJoint element",
    long_description=long_description,
    author='DataJoint NEURO',
    author_email='info@vathes.com',
    license='MIT',
    url='https://github.com/datajoint/element-calcium-imaging',
    keywords='neuroscience calcium-imaging science datajoint',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    scripts=[],
    install_requires=requirements,
)
