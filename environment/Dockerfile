# hash:sha256:a4ce162989be35ccf1ed1d83917fba93f8c54905f48d0de289020bd801c9dddc
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/pytorch:2.4.0-cuda12.4.0-mambaforge24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.4.0 \
    aind-log-utils==0.2.7 \
    dartsort==0.5.10 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.3
