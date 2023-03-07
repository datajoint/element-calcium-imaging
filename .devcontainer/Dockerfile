FROM mcr.microsoft.com/devcontainers/python:3.9-bullseye

COPY ./requirements.txt /tmp/
RUN \
    # dev setup
    apt update && \
    apt-get install bash-completion graphviz default-mysql-client s3fs procps -y && \
    mkdir /tmp/installs/ && \
    TMPDIR=/tmp/installs/ pip install --cache-dir=/tmp/installs/ --upgrade pip && \
    TMPDIR=/tmp/installs/ pip install --cache-dir=/tmp/installs/ flake8 black pre-commit && \
    # workflow dependencies
    apt-get install gcc ffmpeg libsm6 libxext6 -y && \
    TMPDIR=/tmp/installs/ pip install --cache-dir=/tmp/installs Pygments==2.14.0  && \
    git clone https://github.com/datajoint/CaImAn.git  && \
    TMPDIR=/tmp/installs/ pip install --cache-dir=/tmp/installs -r ./CaImAn/requirements.txt  && \
    TMPDIR=/tmp/installs/ pip install --cache-dir=/tmp/installs ./CaImAn && \
    TMPDIR=/tmp/installs/ pip install --cache-dir=/tmp/installs -r /tmp/requirements.txt && \
    # clean up
    rm -rf /tmp/CaImAn && \
    rm -rf /tmp/installs && \
    rm /tmp/requirements.txt && \
    apt-get clean

ENV DJ_HOST fakeservices.datajoint.io
ENV DJ_USER root
ENV DJ_PASS simple

ENV DJ_PUBLIC_S3_MOUNT_PATH /workspaces/workflow-calcium-imaging/example_data