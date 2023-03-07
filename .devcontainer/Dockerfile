FROM mcr.microsoft.com/devcontainers/python:3.7-bullseye

COPY ./requirements.txt /tmp/
RUN \
    # dev setup
    apt update && \
    apt-get install bash-completion graphviz default-mysql-client s3fs procps -y && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir flake8 black pre-commit && \
    # workflow dependencies
    apt-get install gcc ffmpeg libsm6 libxext6 -y && \
    pip install --no-cache-dir Pygments==2.14.0  && \
    pip install --no-cache-dir scipy==1.10.1  && \
    git clone https://github.com/datajoint/CaImAn.git  && \
    pip install --no-cache-dir -r ./CaImAn/requirements.txt  && \
    pip install --no-cache-dir ./CaImAn && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir git+https://github.com/datajoint/suite2p.git@nd2support && \
    # clean up
    rm -rf /tmp/CaImAn && \
    rm /tmp/requirements.txt && \
    apt-get clean

ENV DJ_HOST fakeservices.datajoint.io
ENV DJ_USER root
ENV DJ_PASS simple

ENV DJ_PUBLIC_S3_MOUNT_PATH /workspaces/workflow-calcium-imaging/example_data