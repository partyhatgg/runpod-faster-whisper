# Use nvidia cuda image with cudnn
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

LABEL org.opencontainers.image.source=https://github.com/partyhatgg/runpod-faster-whisper
LABEL org.opencontainers.image.description="A slimmer, more efficient Faster Whisper image for use with the RunPod serverless platform."
LABEL org.opencontainers.image.licenses=MIT

ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash

ENV HF_HOME=/runpod-volume/.cache/huggingface

# NOTICE: This variable will cause uv sync to uninstall system dependencies that are not in the pyproject.toml file.
# This includes Jupyter, which is installed by default in the base image. 
# You can avoid this by unsetting UV_PROJECT_ENVIRONMENT to use a venv or switching to pip to manage system packages.
ENV UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /opt/worker

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

COPY src ./src

CMD ["python", "-m", "src.handler"]
