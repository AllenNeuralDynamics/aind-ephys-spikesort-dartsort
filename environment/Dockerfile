# hash:sha256:6d353e39250f577b0d33ba72b92e31c9c7ad84df665566a98b79c00b37d21061
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/pytorch:2.4.0-cuda12.4.0-mambaforge24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.8.1 \
    aind-log-utils==0.2.7 \
    dartsort==0.5.11 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.7
