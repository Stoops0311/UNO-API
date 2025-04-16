# UNO-API

RunPod Serverless UNO API Worker

This repository implements a serverless API on RunPod that leverages the UNO model to generate images based on:
1. A user-supplied text prompt.
2. An input image URL.

## Project Overview

- **builder/**: Scripts to download and cache model checkpoints at build time.
- **models/**: Pre-downloaded UNO model weights.
- **src/handler.py**: Main API handler. Downloads the input image, invokes the UNO inference pipeline, and returns the generated image.
- **requirements.txt**: Python dependencies (UNO, torch, accelerate, transformers, requests, etc.).
- **Dockerfile**: Container setup, installs dependencies, runs download script, and configures the worker.
- **worker-config.json**: Defines the API schema for RunPod's UI (fields: `prompt`, `image_url`).
- **plan.md**: Detailed development plan and project milestones.

## Getting Started

1. Build the Docker image:
   ```bash
   docker build -t uno-api .
   ```
2. Deploy to RunPod endpoint or run locally:
   ```bash
   docker run --rm -p 8080:8080 uno-api
   ```
3. Send a POST request to `/` with JSON payload:
   ```json
   {
     "prompt": "A clock on the beach under a red sun umbrella",
     "image_url": "https://example.com/clock.png"
   }
   ```

Response:
```json
{
  "image": "<base64-data-or-url>",
  "metadata": { "model": "flux-dev", "time_ms": 12345 }
}
```

Refer to [plan.md](./plan.md) for full development roadmap.
