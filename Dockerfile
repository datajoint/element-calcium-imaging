# TODO update all comands with datajoint repo (kabilar -> datajoint)

FROM jupyter/minimal-notebook:hub-1.4.1

WORKDIR /main/workflow-calcium-imaging

USER root

RUN apt update -y

# Install pip
RUN apt install python3-pip -y

# Set environment variable for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install git
RUN apt install git-all -y

# Install otumat depedency
RUN pip install cryptography==3.3.2

# Install element-data-loader and CaImAn dependencies
RUN pip install --use-deprecated=legacy-resolver "element-data-loader[caiman_requirements] @ git+https://github.com/datajoint/element-data-loader"

# Install CaImAn, Suite2p, Scanreader, Scanbox reader
RUN pip install --use-deprecated=legacy-resolver --ignore-installed "element-data-loader[sbxreader,scanreader,caiman,suite2p] @ git+https://github.com/datajoint/element-data-loader"

# TODO remove this section once the element is updated on PyPI
RUN pip install git+https://github.com/datajoint/element-calcium-imaging.git

# Install workflow-calcium-imaging dependencies (datajoint and elements).  Required when not installing workflow-calcium-imaging.
RUN pip install -r https://raw.githubusercontent.com/kabilar/workflow-calcium-imaging/main/requirements.txt

# Install workflow-calcium-imaging
RUN pip install git+https://github.com/kabilar/workflow-calcium-imaging.git

# Install pytest requirements
RUN pip install -r https://raw.githubusercontent.com/kabilar/workflow-calcium-imaging/docker/requirements_test.txt

USER 1000
