# hash:sha256:c141e046e6b15a2168ca34197d1210eba0ac27ae4a1fac1b38926fe4f382d5c5
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/cuda12-runtime-uv:main-5692e50

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

ENV NUMBA_THREADING_LAYER=tbb

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libtbb-dev=2021.11.0-2ubuntu2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U --no-cache-dir \
    aind-data-schema==2.8.1 \
    dartsort==0.5.21 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.7 \
    torch==2.13.0 \
    torchaudio==2.11.0 \
    torchvision==0.28.0

COPY postInstall /
RUN --mount=type=secret,id=secrets . /run/secrets/secrets \
    && /postInstall
