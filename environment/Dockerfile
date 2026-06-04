# hash:sha256:5a28bc01a7189772150a70ed46f6716045e9421ac54953689aeb819d07165cb6
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/pytorch:2.4.0-cuda12.4.0-mambaforge24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.4.0 \
    aind-log-utils==0.2.7 \
    dartsort==0.5.9 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.3
