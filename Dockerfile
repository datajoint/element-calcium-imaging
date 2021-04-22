FROM ninai/pipeline:base

RUN mkdir /main && mkdir /main/workflow-calcium-imaging

WORKDIR /main/workflow-calcium-imaging

RUN pip3 install --upgrade pip

# Install CaImAn latest version
#RUN pip3 install git+https://github.com/flatironinstitute/CaImAn

# Install CaImAn dependencies
RUN pip3 install pynwb holoviews

# Workflow
RUN git clone https://github.com/ttngu207/workflow-calcium-imaging.git .

RUN pip3 install sbxreader
RUN pip3 install .
RUN pip3 install -r requirements_test.txt
