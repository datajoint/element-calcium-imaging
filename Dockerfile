FROM datajoint/djlab:py3.7-debian

RUN mkdir /main/workflow-calcium-imaging

WORKDIR /main/workflow-calcium-imaging

RUN git clone https://github.com/ttngu207/workflow-calcium-imaging.git .

RUN pip install .
RUN pip install -r requirements_test.txt