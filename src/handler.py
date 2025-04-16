import os
import time
import uuid
import tempfile
import logging

import requests
from PIL import Image
from accelerate import Accelerator
from b2sdk.v2 import InMemoryAccountInfo, B2Api

from uno.flux.pipeline import UNOPipeline, preprocess_ref

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Accelerator and UNO pipeline
accelerator = Accelerator()
MODEL_TYPE = os.getenv("MODEL_TYPE", "flux-dev")
OFFLOAD = os.getenv("OFFLOAD", "False").lower() == "true"
ONLY_LORA = os.getenv("ONLY_LORA", "True").lower() == "true"
LORA_RANK = int(os.getenv("LORA_RANK", "512"))

pipeline = UNOPipeline(
    MODEL_TYPE,
    accelerator.device,
    offload=OFFLOAD,
    only_lora=ONLY_LORA,
    lora_rank=LORA_RANK
)

# Backblaze B2 setup
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APPLICATION_KEY")
B2_BUCKET = os.getenv("B2_BUCKET_NAME")
if not (B2_KEY_ID and B2_APP_KEY and B2_BUCKET):
    logger.error("Missing B2 credentials")
    raise RuntimeError("B2_KEY_ID, B2_APPLICATION_KEY, and B2_BUCKET_NAME must be set")

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
bucket = b2_api.get_bucket_by_name(B2_BUCKET)

# Handler function
def handler(job):
    start_time = time.time()
    inp = job.get("input", {})
    prompt = inp.get("prompt")
    image_url = inp.get("image_url")
    if not prompt or not image_url:
        return {"error": "Both 'prompt' and 'image_url' are required"}

    # Download input image
    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        tmp_in = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_in.write(resp.content)
        tmp_in.flush()
        img = Image.open(tmp_in.name).convert("RGB")
    except Exception as e:
        logger.error("Failed to download image", exc_info=True)
        return {"error": f"Failed to download image: {e}"}

    # Preprocess reference image
    ref_size_env = int(os.getenv("REF_SIZE", "-1"))
    ref_size = ref_size_env if ref_size_env != -1 else 512
    ref_imgs = [preprocess_ref(img, ref_size)]

    # Run UNO inference
    try:
        output_img = pipeline(
            prompt=prompt,
            width=int(os.getenv("WIDTH", "512")),
            height=int(os.getenv("HEIGHT", "512")),
            guidance=float(os.getenv("GUIDANCE", "4")),
            num_steps=int(os.getenv("NUM_STEPS", "25")),
            seed=int(time.time() * 1000) % (2**31),
            ref_imgs=ref_imgs,
            pe=os.getenv("PE", "d")
        )
    except Exception as e:
        logger.error("Inference failed", exc_info=True)
        return {"error": f"Inference failed: {e}"}

    # Save and upload output image
    try:
        tmp_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        output_img.save(tmp_out.name)
        tmp_out.flush()
        file_name = f"{uuid.uuid4()}.png"
        bucket.upload_local_file(local_file=tmp_out.name, file_name=file_name)
        file_url = b2_api.get_download_url_for_file_name(B2_BUCKET, file_name)
    except Exception as e:
        logger.error("Upload to B2 failed", exc_info=True)
        return {"error": f"Upload to Backblaze B2 failed: {e}"}

    duration_ms = int((time.time() - start_time) * 1000)
    metadata = {"model": MODEL_TYPE, "time_ms": duration_ms, "b2_file": file_name}

    return {"image": file_url, "metadata": metadata}

# Start serverless handler
import runpod
runpod.serverless.start({"handler": handler})
