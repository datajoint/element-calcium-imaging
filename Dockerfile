FROM ubuntu:20.04

WORKDIR /main/workflow-calcium-imaging

RUN apt update -y

# Install pip
RUN apt install python3-pip -y

# Set environment variable for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install git
RUN apt install git-all -y

# Install CaImAn dependencies
RUN pip install "element-data-loader[caiman_requirements] @ git+https://github.com/kabilar/element-data-loader" # TODO update with datajoint repo

# Install CaImAn, Suite2p, Scanreader, Scanbox reader
RUN pip install --ignore-installed "element-data-loader[sbxreader,scanreader,caiman,suite2p] @ git+https://github.com/kabilar/element-data-loader" # TODO update with datajoint repo

# Install otumat depedency
RUN pip install cryptography==3.3.2

# Install workflow-calcium-imaging
RUN git clone https://github.com/datajoint/workflow-calcium-imaging.git .
RUN pip install .

# Install pytest requirements
RUN pip install -r requirements_test.txt
