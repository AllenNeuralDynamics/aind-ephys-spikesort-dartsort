# hash:sha256:ce6cdd442a1155a4bb8cc49458de3e0d7f71fab5193bdb93930ebcdfd5301209
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/pytorch:2.4.0-cuda12.4.0-mambaforge24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.4.0 \
    aind-log-utils==0.2.7 \
    cupy-cuda12x==14.0.1 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.3

COPY postInstall /
RUN --mount=type=secret,id=secrets . /run/secrets/secrets \
    && /postInstall
