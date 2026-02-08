import os
import sys
import gc
import torch
import yt_dlp
from dotenv import load_dotenv
from faster_whisper import WhisperModel

# 1. LOAD ENV IMMEDIATELY
# This ensures HuggingFace/Torch caches point to E:/AI_Video_Engine/cache
# before any heavy libraries are imported.
load_dotenv()


class VideoIngestor:
    def __init__(self):
        # Determine Root Directory (Compatible with PyInstaller & Dev)
        if getattr(sys, "frozen", False):
            # If frozen, we want the folder containing the .exe
            self.root_dir = os.path.dirname(sys.executable)
        else:
            # If dev, go up one level from src/
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.root_dir = os.path.dirname(base_dir)

        # Force local temp directory if possible, to avoid C: drive usage
        self.temp_dir = os.path.join(self.root_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)

    def download(
        self, url, start_time=None, end_time=None, resolution="1080", logger=None
    ):
        """
        Downloads a video (or segment) from YouTube.
        start_time/end_time can be in seconds or "HH:MM:SS" / "MM:SS" format.
        resolution: "360", "480", "720", "1080"
        """
        print(f"⬇️  Starting download for: {url} | Res: {resolution}p")

        # Configure yt-dlp
        # Format: best video with height <= resolution
        res_format = f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best"

        ydl_opts = {
            "format": res_format,
            "outtmpl": f"{self.temp_dir}/%(id)s.%(ext)s",
            "paths": {
                "home": self.temp_dir,
                "temp": self.temp_dir,
            },
            "noplaylist": True,
            "quiet": False,
            "no_warnings": True,
            # CRITICAL FIX: 'download_sections' is the correct key, but let's ensure it's not overridden
            # and that we are using a compatible version of yt-dlp.
            # Also, 'force_keyframes_at_cuts' helps with accuracy.
            "force_keyframes_at_cuts": True,
            # PERFORMANCE: Enable concurrent fragment downloads (4 threads)
            "concurrent_fragment_downloads": 4,
            # PERFORMANCE: Larger buffer for better disk I/O
            "buffersize": 1024 * 1024,  # 1MB buffer
        }

        # Handle Clipping (Partial Download)
        if start_time or end_time:
            s = start_time if start_time else "0"
            e = end_time if end_time else "inf"
            msg = f"✂️  Downloading segment: {s} to {e}"
            print(msg)
            if logger:
                logger.log(msg, "INFO")

            # Use 'download_ranges' callback approach if sections fail,
            # but 'download_sections' is the modern standard.
            # We will strictly enforce the syntax.
            def timestamp_to_seconds(ts):
                return self._parse_time(ts)

            start_sec = timestamp_to_seconds(s)
            end_sec = timestamp_to_seconds(e)

            # USE EXTERNAL DOWNLOADER (FFmpeg) - Most reliable for partials
            ydl_opts["download_sections"] = [
                {
                    "start_time": start_sec,
                    "end_time": end_sec,
                    "title": "Analysis_Segment",
                }
            ]
            ydl_opts["external_downloader"] = "ffmpeg"
            ydl_opts["external_downloader_args"] = {
                "ffmpeg_i": ["-ss", str(start_sec), "-to", str(end_sec)]
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                title = info.get("title", "Unknown_Video")
                print(f"✅ Download Complete: {filename}")
                return filename, title
        except Exception as e:
            print(f"❌ Download Error: {e}")
            return None, None

    def get_video_info(self, url):
        """
        Fetches metadata (duration, title) without downloading.
        Returns: (duration_seconds, title)
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("duration", 0), info.get("title", "Unknown")
        except Exception as e:
            print(f"❌ Metadata Error: {e}")
            return 0, None

    def _parse_time(self, t):
        """Helper to convert HH:MM:SS or MM:SS to seconds."""
        if isinstance(t, (int, float)):
            return float(t)
        if t == "inf":
            return float("inf")

        parts = list(map(int, t.split(":")))
        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        return float(parts[0])  # Just seconds


class Transcriber:
    def __init__(self, model_size="large-v3-turbo"):
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        self.model = None

    def load_model(self):
        if self.model is None:
            print(
                f"🧠 Loading Whisper Model ({self.model_size}) to {self.device.upper()}..."
            )
            # Define local model path (Compatible with PyInstaller)
            if getattr(sys, "frozen", False):
                root_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                root_dir = os.path.dirname(base_dir)

            model_cache_dir = os.path.join(root_dir, "models", "whisper")

            # This downloads (or loads) the model to local models/whisper
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=model_cache_dir,
            )
            msg = f"✅ Model Loaded on {self.device.upper()} (Compute: {self.compute_type})"
            print(msg)
            # We can't easily access the logger from here without passing it in,
            # but this print will be caught if the caller logs it.
            # However, let's try to print to a file if we can, or just rely on the caller.
            # actually, let's just leave the print, main_ui.py handles capturing some things,
            # but ideally we want this in the log file.

    def transcribe(self, video_path, logger=None):
        if not self.model:
            self.load_model()
            if logger:
                logger.log(
                    f"🚀 Whisper Model Initialized on {self.device.upper()}", "INFO"
                )

        msg = "🎙️  Transcribing audio (Generating Word-Level Timestamps)..."
        print(msg)
        if logger:
            logger.log(msg, "INFO")

        # word_timestamps=True is required for precise cutting later
        # vad_filter=True prevents the model from hallucinating in silent parts
        segments, info = self.model.transcribe(
            video_path, beam_size=5, word_timestamps=True, vad_filter=True
        )

        msg = f"   Detected Language: {info.language.upper()} (Probability: {info.language_probability:.2f})"
        print(msg)
        if logger:
            logger.log(msg, "INFO", "CYAN")

        word_list = []

        # Iterate through segments and flatten into a simple list of words
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    word_data = {
                        "start": word.start,
                        "end": word.end,
                        "word": word.word.strip(),
                    }
                    word_list.append(word_data)
                    # Optional: Print progress dots
                    print(".", end="", flush=True)

        msg = f"\n✅ Transcription Complete. {len(word_list)} words extracted."
        print(msg)
        if logger:
            logger.log(msg, "INFO")

        # AUTO-CLEANUP: Free VRAM immediately after use
        self.free_memory()

        return word_list

    def free_memory(self):
        """
        CRITICAL for 8GB VRAM:
        Destroys the Whisper model and forces CUDA to release memory
        so Ollama (LLM) can run without crashing.
        """
        print("🧹 Cleaning up GPU VRAM...")
        if self.model:
            del self.model
            self.model = None

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        current_vram = torch.cuda.memory_allocated(0) / 1024**2
        print(f"✅ VRAM Cleared. Current usage: {current_vram:.2f} MB")

        # Give the GPU driver a moment to stabilize before next AI task (Ollama)
        import time

        time.sleep(1)


# --- Usage Example ---
if __name__ == "__main__":
    # 1. Test URL (Short video for quick testing)
    TEST_URL = "https://youtu.be/9AjDaW3G-fQ?si=pPgyqFXjmuun0OLA"

    # 2. Ingest
    ingestor = VideoIngestor()
    video_path = ingestor.download(TEST_URL)

    if video_path:
        # 3. Transcribe
        transcriber = Transcriber()
        words = transcriber.transcribe(video_path)

        # 4. Show sample output
        print("\n--- First 5 Words ---")
        print(words[:5])
