# Dockerfile for UNO-API serverless worker
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Arguments and environment variables
ARG HF_HUB_TOKEN
ENV HF_HUB_TOKEN=${HF_HUB_TOKEN}
ARG B2_KEY_ID
ARG B2_APPLICATION_KEY
ARG B2_BUCKET_NAME
ENV B2_KEY_ID=${B2_KEY_ID}
ENV B2_APPLICATION_KEY=${B2_APPLICATION_KEY}
ENV B2_BUCKET_NAME=${B2_BUCKET_NAME}
ENV FLUX_DEV=/models/flux/flux1-dev.safetensors
ENV AE=/models/flux/ae.safetensors
ENV CLIP=/models/clip
ENV T5=/models/t5
ENV LORA=/models/loras/dit_lora.safetensors

# Install system dependencies and Python
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y git wget curl python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Prepare model download directories
RUN mkdir -p /models/flux /models/clip /models/t5

# Download UNO model weights and encoders
RUN huggingface-cli download black-forest-labs/FLUX.1-dev flux1-dev.safetensors --local-dir /models/flux --token $HF_HUB_TOKEN && \
    huggingface-cli download black-forest-labs/FLUX.1-dev ae.safetensors --local-dir /models/flux --token $HF_HUB_TOKEN && \
    huggingface-cli download bytedance-research/UNO dit_lora.safetensors --local-dir /models/loras --token $HF_HUB_TOKEN && \
    huggingface-cli download openai/clip-vit-large-patch14 --local-dir /models/clip && \
    huggingface-cli download xlabs-ai/xflux_text_encoders --local-dir /models/t5

# Copy source code
COPY . .

# Expose port
EXPOSE 8080

# Default command
CMD ["python", "-u", "src/handler.py"]
