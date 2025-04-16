# UNO-API: Serverless UNO Image Generation Worker for RunPod

This repository contains a serverless worker designed to run on [RunPod](https://runpod.io). It leverages the [UNO (FLUX.1-dev + LoRA)](https://github.com/bytedance-research/UNO) model to generate images based on a text prompt and a reference image URL. The generated image is uploaded to Backblaze B2, and a downloadable URL is returned.

## ✨ Features

*   **UNO Model Integration:** Utilizes the high-quality UNO model for image generation, combining the power of FLUX.1-dev with a dedicated LoRA.
*   **RunPod Optimized:** Built for serverless deployment, minimizing cold-start times and runtime costs.
*   **Model Baking:** All required models (FLUX, AE, CLIP, T5, LoRA) are downloaded and baked into the Docker image during the build process.
*   **Backblaze B2 Integration:** Securely uploads generated images to a B2 bucket and returns a URL.
*   **Configurable:** Uses `worker-config.json` for RunPod UI integration and environment variables for model/diffusion parameters.
*   **Secure Credentials:** Handles Hugging Face and B2 credentials via Docker build arguments.

## 🛠️ Setup & Build

### Prerequisites

*   [Docker](https://www.docker.com/) installed.
*   [Hugging Face Hub](https://huggingface.co/) account and access token (`HF_HUB_TOKEN`).
*   [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html) account, bucket, Key ID (`B2_KEY_ID`), and Application Key (`B2_APPLICATION_KEY`).

### Building the Docker Image

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Stoops0311/uno-api.git
    cd uno-api
    ```

2.  **Clean up Docker (Optional but Recommended):**
    ```bash
    # Remove stopped containers, unused networks, dangling images, build cache
    docker system prune -af
    # Remove unused volumes (use with caution)
    docker volume prune -f
    ```

3.  **Build the image:**
    Replace the placeholder values with your actual credentials. The image will be tagged for your Docker Hub username (replace `your_dockerhub_username` if different).
    ```bash
    docker build \
      --build-arg HF_HUB_TOKEN="YOUR_HF_HUB_TOKEN" \
      --build-arg B2_KEY_ID="YOUR_B2_KEY_ID" \
      --build-arg B2_APPLICATION_KEY="YOUR_B2_APP_KEY" \
      --build-arg B2_BUCKET_NAME="YOUR_B2_BUCKET_NAME" \
      -t your_dockerhub_username/uno-api:latest . | tee build.log
    ```
    *   `YOUR_HF_HUB_TOKEN`: Your Hugging Face token (e.g., `hf_...`).
    *   `YOUR_B2_KEY_ID`: Your Backblaze B2 Key ID.
    *   `YOUR_B2_APPLICATION_KEY`: Your Backblaze B2 Application Key.
    *   `YOUR_B2_BUCKET_NAME`: The name of your Backblaze B2 bucket.
    *   `your_dockerhub_username`: Your Docker Hub username (e.g., `nuaym`).
    *   The `| tee build.log` saves the full build output to `build.log`.

4.  **(Optional) Push to Docker Hub:**
    ```bash
    docker login
    docker push your_dockerhub_username/uno-api:latest
    ```

## 🚀 API Usage (RunPod Serverless)

When deployed as a RunPod serverless endpoint, the worker expects the following input payload:

### Input Schema

```json
{
  "input": {
    "prompt": "A high-resolution photo of a futuristic cityscape at sunset",
    "image_url": "https://example.com/path/to/your/reference_image.jpg"
  }
}
```

*   `prompt` (string, required): The text prompt describing the desired output image.
*   `image_url` (string, required): A publicly accessible URL to the reference image.

### Output Schema

**Success:**

```json
{
  "image": "https://f005.backblazeb2.com/file/your-b2-bucket/generated_image_uuid.png",
  "metadata": {
    "model": "flux-dev", // Or the model type used
    "time_ms": 15234,    // Generation time in milliseconds
    "b2_file": "generated_image_uuid.png" // Filename in B2
  }
}
```

**Error:**

```json
{
  "error": "Descriptive error message (e.g., Failed to download image: 404 Client Error)"
}
```

## ⚙️ Configuration (Environment Variables)

While `prompt` and `image_url` are provided via the job input, other parameters can be configured using environment variables set via the RunPod Endpoint configuration (`worker-config.json`) or directly in the template:

*   **Model Parameters:**
    *   `MODEL_TYPE`: UNO model variant (`flux-dev`, `flux-dev-fp8`, `flux-schnell`). Default: `flux-dev`.
    *   `OFFLOAD`: Offload model to CPU (`True`/`False`). Default: `False`.
    *   `ONLY_LORA`: Use only LoRA weights (`True`/`False`). Default: `True`.
    *   `LORA_RANK`: Rank for LoRA layers. Default: `512`.
*   **Diffusion Parameters:**
    *   `REF_SIZE`: Size to preprocess reference image to (-1 for auto). Default: `-1`.
    *   `WIDTH`: Output image width. Default: `512`.
    *   `HEIGHT`: Output image height. Default: `512`.
    *   `NUM_STEPS`: Number of sampling steps. Default: `25`.
    *   `GUIDANCE`: Guidance scale. Default: `4.0`.
    *   `PE`: Positional encoding mode (`d`, `h`, `w`, `o`). Default: `d`.

*   **Credentials (Set via Docker build args, accessible as ENV vars):**
    *   `HF_HUB_TOKEN`: Hugging Face Token.
    *   `B2_KEY_ID`: Backblaze B2 Key ID.
    *   `B2_APPLICATION_KEY`: Backblaze B2 Application Key.
    *   `B2_BUCKET_NAME`: Backblaze B2 Bucket Name.

## 📦 Models Included

The following models are downloaded during the Docker build and baked into the image in the `/models` directory:

*   **FLUX:** `black-forest-labs/FLUX.1-dev` (`flux1-dev.safetensors`) -> `/models/flux/`
*   **AE:** `black-forest-labs/FLUX.1-dev` (`ae.safetensors`) -> `/models/flux/`
*   **UNO LoRA:** `bytedance-research/UNO` (`dit_lora.safetensors`) -> `/models/loras/`
*   **CLIP:** `openai/clip-vit-large-patch14` -> `/models/clip/`
*   **T5:** `xlabs-ai/xflux_text_encoders` -> `/models/t5/`

Environment variables (`FLUX_DEV`, `AE`, `CLIP`, `T5`, `LORA`) in the Dockerfile point the handler to these locations.

## 📄 License

This project uses components under various licenses. Please refer to the licenses of the underlying models and libraries (UNO, Flux, Transformers, etc.). The handler code itself is provided under the Apache 2.0 License (or choose another if preferred).
