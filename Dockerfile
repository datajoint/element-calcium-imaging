ARG PY_VER
ARG DISTRO
ARG IMAGE
ARG PKG_NAME
ARG PKG_VERSION

FROM datajoint/${IMAGE}:py${PY_VER}-${DISTRO}
COPY --chown=dja:anaconda ./requirements.txt ./setup.py \
    /main/
COPY --chown=dja:anaconda ./${PKG_NAME} /main/${PKG_NAME}
RUN \
    cd /main && \
    pip install . && \
    rm -R /main/*
WORKDIR /main
