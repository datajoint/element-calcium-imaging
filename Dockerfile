FROM datajoint/djlab:py3.8-debian

USER root
RUN apt-get update -y
RUN apt-get install git -y

USER anaconda
WORKDIR /main/workflow-calcium-imaging
RUN git clone https://github.com/datajoint/workflow-calcium-imaging.git .
RUN pip install .
RUN pip install -r requirements_test.txt

# Install element-inteface and CaImAn dependencies
RUN pip install --use-deprecated=legacy-resolver "element-inteface[caiman_requirements] @ git+https://github.com/datajoint/element-inteface"

# Install CaImAn, Suite2p, Scanreader, Scanbox reader
RUN pip install --use-deprecated=legacy-resolver --ignore-installed "element-inteface[sbxreader,scanreader,caiman,suite2p] @ git+https://github.com/datajoint/element-inteface"

