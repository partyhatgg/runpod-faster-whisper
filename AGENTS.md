# AGENTS.md

This file provides guidance to AI agents and coding assistants working with this repository.

## What is This?

This is a **Runpod serverless handler** for transcribing audio using Faster Whisper.

### What is Runpod Serverless?

Runpod is a cloud provider that offers a serverless GPU platform. Unlike traditional serverless (AWS Lambda, etc.), Runpod is designed for GPU workloads:

- The user deploys a Docker container with a handler function (like this project)
- Runpod manages GPU workers that run your container
- Workers auto-scale based on request volume or the time requests spend in queue.
- Each request goes to an available worker; if none exist, one spins up (a traditional serverless cold start)
- Workers stay alive for a configurable time after requests to avoid cold starts

The key difference: you only pay when processing requests, not for idle time.

### What is a Handler?

A Runpod handler is powered by the runpod-python SDK and it is the entry point loaded by serverless workers that processes incoming requests. 

The pattern:

1. **Initialization phase** (once per worker): Load your model, download weights, prepare GPU memory
2. **Request phase** (per request): Receive JSON input, process it, return JSON output

This handler loads Faster Whisper models (medium and turbo) once at startup, then processes transcription requests using those loaded models. This amortizes the expensive model-loading across many requests for the lifecycle of this worker.

## Architecture

This is an intentionally minimal codebase, keeping it that way is crucial. We have three files:

- `src/handler.py` - Handler implementation. Loads Whisper models at startup, exposes `handler()` function that Runpod calls
- `src/predict.py` - Predictor class that wraps Faster Whisper for transcription/translation
- `src/schema.py` - Input validation schema (audio input, model selection, transcription options)

### Supported Models

- `medium` - Balanced speed/accuracy
- `turbo` - Faster, slightly less accurate

### Input Methods

- `audio` - URL to audio file (downloaded by handler)
- `audio_base64` - Base64-encoded audio data

### Output Formats

- `plain_text` - Continuous text
- `formatted_text` - Line-separated text
- `srt` - SubRip subtitle format
- `vtt` - WebVTT subtitle format

## Additional Help

If you need specifics about Runpod Serverless APIs, endpoints, or deployment:
- Use the `SearchRunpodDocumentation` tool to search Runpod's documentation in real time. If you don't have access to this tool, ask your user to enable the MCP server at `https://docs.runpod.io/mcp`
