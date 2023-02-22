# Note: You can use any Debian/Ubuntu based image you want.
FROM mcr.microsoft.com/devcontainers/python:3.7-bullseye

# --- CONN OPTIONS ---
ENV DJ_HOST fakeservices.datajoint.io
ENV DJ_USER root
ENV DJ_PASS simple

# --- ELEMENT OPTIONS --
ENV ELEMENT calcium-imaging
ENV INSTALL_EDITABLE false
ENV INSTALL_CAIMAN false
ENV GITHUB_USER datajoint

# CAIMAN NOTES - M1 had issues with:
# apt-get install ffmpeg libhdf5-dev -y && \
# FFMPEG https://stackoverflow.com/questions/42589892/how-to-install-ffmpeg-for-ubuntu-using-command-line
# CONDA: linux-aarch64 cannot find z5py or tensorflow
# ND2 installation issues
    # conda install -c conda-forge imagecodecs && \

RUN \
    echo "--- DATAJOINT ---" && \
    apt update && \
    apt-get install bash-completion graphviz default-mysql-client -y && \
    apt-get install gcc -y && \
    pip install --upgrade pip && \
    pip install flake8 black faker ipykernel pytest pytest-cov pre-commit datajoint && \
    alias ll='ls -aGg' && \
    echo "--- ELEMENTS ---" && \
    if [ $INSTALL_EDITABLE = true ]; then \
        for f in lab animal session interface $ELEMENT; do \
            git clone https://github.com/${GITHUB_USER}/element-${f} /workspaces/element-${f} || \
            true && \
            pip install -e /workspaces/element-${f}; \
        done; \
    else  \
        for f in lab animal session interface $ELEMENT; do \
            pip install git+https://github.com/${GITHUB_USER}/element-${f}.git; \
        done; \
    fi && \
    if [ $INSTALL_CAIMAN = true ]; then \
        echo "--- CAIMAN ---" && \
        /bin/bash -c 'conda install -n base -c conda-forge -c anaconda -y mamba' && \
        git clone --branch master https://github.com/datajoint-company/CaImAn /workspaces/CaImAn/ || true && \
        /bin/bash -c 'conda env update --n base -f /workspaces/CaImAn/environment-minimal.yml -y' && \
        pip install /workspaces/CaImAn/ && pip install numpy==1.21; \
    fi && \
    echo "--- DONE ---"
