FROM datajoint/djlab:py3.7-debian

RUN mkdir /main/workflow-calcium-imaging

WORKDIR /main/workflow-calcium-imaging

#RUN conda config --set channel_priority flexible
#RUN conda update conda && conda install -c conda-forge caiman

RUN pip install sbxreader

RUN git clone https://github.com/ttngu207/workflow-calcium-imaging.git .

RUN pip install .
RUN pip install -r requirements_test.txt