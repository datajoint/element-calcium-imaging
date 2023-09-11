#!/usr/bin/env python
from os import path
from setuptools import find_packages, setup
import urllib.request

pkg_name = "element_calcium_imaging"
here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), "r") as f:
    long_description = f.read()

with open(path.join(here, pkg_name, "version.py")) as f:
    exec(f.read())

with urllib.request.urlopen(
    "https://raw.githubusercontent.com/flatironinstitute/CaImAn/master/requirements.txt"
) as f:
    caiman_requirements = f.read().decode("UTF-8").split("\n")

caiman_requirements.remove("")
caiman_requirements.append("future")

setup(
    name=pkg_name.replace("_", "-"),
    version=__version__,  # noqa: F821
    description="Calcium Imaging DataJoint Element",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DataJoint",
    author_email="info@datajoint.com",
    license="MIT",
    url=f'https://github.com/datajoint/{pkg_name.replace("_", "-")}',
    keywords="neuroscience calcium-imaging science datajoint",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    scripts=[],
    install_requires=[
        "datajoint>=0.13.0",
        "ipykernel>=6.0.1",
        "ipywidgets",
        "plotly",
    ],
    extras_requires={
        "caiman_requirements": [caiman_requirements],
        "caiman": ["caiman @ git+https://github.com/datajoint/CaImAn"],
        "elements": [
            "element-animal>=0.1.8",
            "element-event>=0.2.3",
            "element-interface>=0.6.0",
            "element-lab>=0.3.0",
            "element-session>=0.1.5",
        ],
        "extract": ["matlabengine", "scipy"],
        "nd2": ["nd2"],
        "sbxreader": ["sbxreader @ git+https://github.com/jcouto/sbxreader"],
        "scanreader": ["scanreader @ git+https://github.com/atlab/scanreader"],
        "suite2p": ["suite2p[io]>=0.12.1"],
        "tests": ["pytest", "pytest-cov", "shutils"],
    },
)
