# Note: You can use any Debian/Ubuntu based image you want. 
FROM mcr.microsoft.com/devcontainers/python:3.7-bullseye

RUN \
    apt update && \
    apt-get install bash-completion graphviz default-mysql-client s3fs procps -y && \
    pip install flake8 black faker ipykernel pytest pytest-cov datajoint
RUN \
    mkdir /home/vscode/example_data && \
    chown vscode:vscode /home/vscode/example_data
ENV DJ_HOST fakeservices.datajoint.io
ENV DJ_USER root
ENV DJ_PASS simple
