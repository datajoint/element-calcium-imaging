#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys

here = path.abspath(path.dirname(__file__))

long_description = """"
Canonical DataJoint pipeline for calcium imaging with CaImAn pipeline for analysis
"""

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='canonical-imaging',
    version='0.0.1',
    description="Canonical Imaging Pipeline",
    long_description=long_description,
    author='DataJoint NEURO',
    author_email='info@vathes.com',
    license='MIT',
    url='https://github.com/vathes/canonical-imaging',
    keywords='neuroscience calcium-imaging science datajoint',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    scripts=[],
    install_requires=requirements,
)
