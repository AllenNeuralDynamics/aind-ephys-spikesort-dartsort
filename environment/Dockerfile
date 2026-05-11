# TODO: choose an appropriate base image.
#
# Option A — use an existing CodeOcean base image that already bundles your sorter:
#   e.g. codeocean/kilosort4-base:4.0.30_cuda-12.0.0  (GPU sorters)
#
# Option B — start from a plain Python image and install everything via pip:
#   e.g. codeocean/mambaforge3:24.5.0-0-python3.12.4-ubuntu22.04
#
# See https://hub.docker.com/u/codeocean for available images.

ARG REGISTRY_HOST
# TODO: replace with the actual base image
FROM $REGISTRY_HOST/codeocean/mambaforge3:24.5.0-0-python3.12.4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-askpass /

# TODO: add or remove system packages as needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential=12.9ubuntu3 \
    && rm -rf /var/lib/apt/lists/*

# TODO: pin the exact package versions required by your sorter
RUN pip install -U --no-cache-dir \
    aind-data-schema==2.4.0 \
    aind-log-utils==0.2.3 \
    spikeinterface[full]==0.103.0
# TODO: add your sorter's pip package here, e.g.:
#   my-sorter-package==x.y.z
