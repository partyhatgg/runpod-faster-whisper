# Use specific version of nvidia cuda image
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Labeling for GHCR, then we'll build the image :)
LABEL org.opencontainers.image.source=https://github.com/partyhatgg/runpod-faster-whisper
LABEL org.opencontainers.image.description="A slimmer, more efficient Faster Whisper image for use with the RunPod serverless platform."
LABEL org.opencontainers.image.licenses=MIT

# Set shell and noninteractive environment variables
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash

# Set working directory
WORKDIR /

# Update and upgrade the system packages (Worker Template)
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends git wget curl software-properties-common python3-pip python-is-python3 libcudnn8 && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list

# Install Python dependencies (Worker Template)
COPY builder/requirements.txt /requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /requirements.txt --no-cache-dir && \
    rm /requirements.txt

# Copy and run script to fetch models
COPY builder/fetch_models.py /fetch_models.py
RUN python /fetch_models.py && rm /fetch_models.py

# Copy source code into image
COPY src .

# Set default command
CMD ["python", "-u", "/rp_handler.py"]
