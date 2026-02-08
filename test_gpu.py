import torch
import os
from dotenv import load_dotenv
from faster_whisper import WhisperModel

# Load the environment variables to ensure the cache is on E:
load_dotenv()

print(f"--- System Check ---")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU Device: {torch.cuda.get_device_name(0)}")
    # Check if we are pointing to E: drive
    print(f"HF_HOME Env: {os.getenv('HF_HOME')}")
else:
    print("❌ CUDA NOT FOUND. Check your install.bat logs for errors.")

# Test Faster-Whisper
print("\n--- Testing Faster-Whisper Load (Moving to GPU) ---")
try:
    # This will download a tiny (~50MB) model to E:/AI_Video_Engine/cache/huggingface
    model = WhisperModel("tiny", device="cuda", compute_type="float16")
    print("✅ Model loaded successfully into RTX 4060 VRAM!")
except Exception as e:
    print(f"❌ Error: {e}")
