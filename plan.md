# UNO-API RunPod Worker: Step-by-Step Detailed Plan

## 1. Project Structure

```
UNO-API/
│
├── builder/                  # Scripts for build-time setup (e.g., model download)
│   └── download_models.sh    # Script to download UNO models
├── models/                   # Directory to store model weights/checkpoints
├── src/                      # Worker source code
│   └── handler.py            # Main handler for processing API requests
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container build instructions
├── worker-config.json        # RunPod endpoint config schema
├── plan.md                   # This detailed plan
└── README.md                 # Project overview and usage
```

## 2. Preparation and Setup

### 2.1. Clone and Initialize
- Create the UNO-API directory and subdirectories as above.
- Copy or symlink UNO codebase if needed, or install via pip if published.

### 2.2. Model Download Script
- Write `builder/download_models.sh` to download all required UNO model weights from Hugging Face to `/models`.
- The script should:
  - Use `huggingface-cli` or `python -m huggingface_hub` to fetch each required checkpoint.
  - Validate downloads and exit with error if any fail.

### 2.3. Dockerfile Setup
- Base image: Use a CUDA-enabled Python image (e.g., `nvidia/cuda:12.2.0-cudnn8-runtime-ubuntu22.04` or similar).
- Install system dependencies (git, wget, etc.).
- Copy `requirements.txt` and install Python dependencies (UNO, torch, accelerate, etc.).
- Copy UNO codebase if not pip-installable.
- Copy `builder/download_models.sh` and run it to populate `/models` at build time.
- Set environment variables (e.g., `FLUX_DEV`, `AE`, etc.) to point to `/models` files.
- Copy `src/handler.py` and set the entrypoint for RunPod.

## 3. API Design

### 3.1. Input Schema (worker-config.json)
- Define fields:
  - `prompt` (string): The user prompt for image generation.
  - `image_url` (string): URL to the input image.
  - (Optional) `model_type`, `width`, `height`, etc. for advanced control.
- Ensure required fields are marked as such.

### 3.2. Output Schema
- Return a JSON object with:
  - `image`: The generated image downloadable URL (since we uploaded to backbalze once the image was generated).
  - `metadata`: Any additional info (e.g., generation time, model used).
  - `error`: Error message if the request fails.

## 4. Handler Logic (src/handler.py)

### 4.1. Input Validation
- Check presence and validity of `prompt` and `image_url`.
- Return error if missing or malformed.

### 4.2. Image Download
- Download the image from `image_url` using `requests` or similar.
- Save to a temporary file in `/tmp` or a designated location.
- Validate that the file is a valid image.

### 4.3. UNO Inference
- Import UNO pipeline (or call inference.py as a subprocess if direct import is problematic).
- Pass the prompt and downloaded image path to the UNO pipeline.
- Ensure environment variables or pipeline arguments point to `/models` for weights.
- Capture the generated output image.

### 4.4. Output Handling
- Convert the generated image to base64 or upload to a storage bucket and return the URL.
- Clean up any temporary files.
- Return the result as JSON.

### 4.5. Error Handling
- Catch and log any errors in download, inference, or output steps.
- Return a clear error message in the response.

## 5. Model Management

### 5.1. Download at Build Time
- Use `builder/download_models.sh` in Dockerfile to fetch all required models during image build.
- Store in `/models` for quick access at runtime.

### 5.2. Environment Variables
- Set `FLUX_DEV`, `AE`, `CLIP`, `T5`, `LORA` env vars to point to files in `/models`.
- Ensure UNO pipeline uses these for loading models.

## 6. Testing and Validation

### 6.1. Local Testing
- Test handler logic locally with sample payloads and images.
- Validate model loading from `/models`.

### 6.2. RunPod Testing
- Deploy to RunPod serverless endpoint.
- Test with actual API requests via the RunPod UI or curl/Postman.

## 7. Documentation

- Document all environment variables, API fields, and usage in README.md.
- Provide example requests and expected responses.

## 8. Optional Enhancements

- Add support for multiple images or advanced UNO parameters.
- Implement caching of results for repeated requests.
- Add monitoring/logging for usage and errors.

---

This plan ensures a robust, reproducible, and scalable UNO-API worker deployment for RunPod serverless endpoints. Each step can be expanded with code and scripts as needed.
