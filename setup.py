#!/usr/bin/env python
import subprocess
from os import path
from setuptools import setup, find_packages


pkg_name = next(p for p in find_packages() if "." not in p)
here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), "r") as f:
    long_description = f.read()

with open(path.join(here, "requirements.txt")) as f:
    requirements = f.read().splitlines()

with open(path.join(here, pkg_name, "version.py")) as f:
    exec(f.read())

# Prerequisite of caiman installation to run its setup.py
subprocess.call(["pip", "install", "numpy", "Cython"])

extras_require = {
    "suite2p": "suite2p @ git+https://github.com/datajoint-company/suite2p.git",
    "caiman": "caiman @ git+https://github.com/datajoint-company/CaImAn.git",
    "readers": [
        "nd2==0.1.6",
        "tifffile==2021.11.2",
        "sbxreader==0.1.6.post1",
        "scanreader @ git+https://github.com/atlab/scanreader.git",
    ],
}

setup(
    name=pkg_name.replace("_", "-"),
    version=__version__,
    description="Calcium Imaging DataJoint element",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DataJoint",
    author_email="info@datajoint.com",
    license="MIT",
    url=f'https://github.com/datajoint/{pkg_name.replace("_", "-")}',
    keywords="neuroscience calcium-imaging science datajoint",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    scripts=[],
    install_requires=requirements,
    extras_require=extras_require,
)
