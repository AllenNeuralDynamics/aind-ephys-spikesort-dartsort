# hash:sha256:193930715973d86fc5572aa28a6ac178e4ceb272b224a95c70fe9f725d215c0c
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/pytorch:2.4.0-cuda12.4.0-mambaforge24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.4.0 \
    aind-log-utils==0.2.7 \
    dartsort==0.5.5 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.3
