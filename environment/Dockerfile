# hash:sha256:d8c192f9a5185b3e2efc020043a52a2fb453094cf76b9670c3e24e3ebdaffff6
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/pytorch:2.4.0-cuda12.4.0-mambaforge24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.8.1 \
    dartsort==0.5.18 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.7

COPY postInstall /
RUN --mount=type=secret,id=secrets . /run/secrets/secrets \
    && /postInstall
