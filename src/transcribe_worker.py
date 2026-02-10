"""
Transcribe Worker - Subprocess Isolation for Whisper

This script runs in a SEPARATE PROCESS to isolate CTranslate2's CUDA
cleanup from the main Flet UI process. When this process exits, the OS
reclaims all GPU memory automatically — no C++ destructor crash.

Usage:
    python transcribe_worker.py <video_path> <output_json_path> [model_size]

Output:
    Writes a JSON file with the word list:
    [{"start": 0.0, "end": 0.5, "word": "Hello"}, ...]

Exit Codes:
    0 = Success (JSON file written)
    1 = Error (check stderr)
"""

import sys
import os
import json

# Ensure project root is on the path for dotenv
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env before importing heavy libs
from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: transcribe_worker.py <video_path> <output_json_path> [model_size]",
            file=sys.stderr,
        )
        sys.exit(1)

    video_path = sys.argv[1]
    output_json_path = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"

    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    print("[WORKER] Starting transcription subprocess", flush=True)
    print(f"[WORKER] Video: {video_path}", flush=True)
    print(f"[WORKER] Model: {model_size}", flush=True)

    try:
        import torch
        from faster_whisper import WhisperModel

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(
            f"[WORKER] 🧠 Loading Whisper Model ({model_size}) to {device.upper()}...",
            flush=True,
        )

        # Model cache directory
        model_cache_dir = os.path.join(BASE_DIR, "models", "whisper")

        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=model_cache_dir,
        )

        print(
            f"[WORKER] ✅ Model Loaded on {device.upper()} (Compute: {compute_type})",
            flush=True,
        )

        # Transcribe
        print("[WORKER] 🎙️  Transcribing audio (Word-Level Timestamps)...", flush=True)

        segments, info = model.transcribe(
            video_path, beam_size=5, word_timestamps=True, vad_filter=True
        )

        print(
            f"[WORKER]    Detected Language: {info.language.upper()} (Probability: {info.language_probability:.2f})",
            flush=True,
        )

        word_list = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    word_list.append(
                        {
                            "start": round(word.start, 3),
                            "end": round(word.end, 3),
                            "word": word.word.strip(),
                        }
                    )
                    print(".", end="", flush=True)

        print(
            f"\n[WORKER] ✅ Transcription Complete. {len(word_list)} words extracted.",
            flush=True,
        )

        # Write results to JSON
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(word_list, f, ensure_ascii=False)

        print(f"[WORKER] ✅ Results written to {output_json_path}", flush=True)

        # NO explicit cleanup! Let the process exit naturally.
        # The OS will reclaim all CUDA memory when this process terminates.
        # This avoids the CTranslate2 C++ destructor segfault entirely.

    except Exception as e:
        import traceback

        print(f"\n[WORKER] ❌ Transcription Error: {e}", file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)

    # Exit with success
    sys.exit(0)


if __name__ == "__main__":
    main()
