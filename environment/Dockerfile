# hash:sha256:6871c42907a3bc1c88df49d26e5111c024d0fbdf1a77127aef65eb7f680793f8
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
    dartsort==0.5.23 \
    scipy==1.17.1 \
    spikeinterface[full]==0.104.7 \
    torch==2.13.0 \
    torchaudio==2.11.0 \
    torchvision==0.28.0

COPY postInstall /
RUN --mount=type=secret,id=secrets . /run/secrets/secrets \
    && /postInstall
