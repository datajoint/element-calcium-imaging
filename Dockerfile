FROM ubuntu:20.04

WORKDIR /main/workflow-calcium-imaging

RUN apt update -y

# Install pip
RUN apt install python3-pip -y

# Set environment variable for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install git
RUN apt install git-all -y

# Install Scanreader
RUN pip install git+https://github.com/atlab/scanreader.git

# Install Scanbox reader
RUN pip install sbxreader

# Install CaImAn dependencies
RUN pip install -r https://raw.githubusercontent.com/flatironinstitute/CaImAn/master/requirements.txt

# Install cv2 dependencies
RUN apt install ffmpeg libsm6 libxext6  -y

# Install CaImAn
RUN pip install git+https://github.com/flatironinstitute/CaImAn

# Install otumat depedency
RUN pip install cryptography==3.3.2

# Install workflow-calcium-imaging
RUN git clone https://github.com/datajoint/workflow-calcium-imaging.git .
RUN pip install .

# Install pytest requirements
RUN pip install -r requirements_test.txt
