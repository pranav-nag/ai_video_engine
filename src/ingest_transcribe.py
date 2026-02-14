import os
import sys

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
        self,
        url,
        start_time=None,
        end_time=None,
        resolution="1080",
        logger=None,
        cancel_event=None,
    ):
        """
        Downloads a video (or segment) from YouTube.
        start_time/end_time can be in seconds or "HH:MM:SS" / "MM:SS" format.
        resolution: "360", "480", "720", "1080"
        cancel_event: optional threading.Event() to stop download
        """
        print(f"⬇️  Starting download for: {url} | Res: {resolution}p")

        # 1. Cancellation Hook
        def progress_hook(d):
            if cancel_event and cancel_event.is_set():
                raise Exception("Download Cancelled by User")

        # 0. FETCH METADATA (Duration) for Strategy Decision
        total_duration, _ = self.get_video_info(url)
        use_full_download = False

        if start_time or end_time:
            s = start_time if start_time else "0"
            e = end_time if end_time else "inf"

            def timestamp_to_seconds(ts):
                return self._parse_time(ts)

            start_sec = timestamp_to_seconds(s)
            end_sec = timestamp_to_seconds(e)
            if end_sec == float("inf"):
                end_sec = total_duration

            wanted_duration = end_sec - start_sec

            # --- SMART DOWNLOAD STRATEGY ---
            # 1. If video is short (< 15 mins), just download FULL. It's faster/safer.
            if total_duration < 900:  # 15 mins
                use_full_download = True
                print(
                    f"⚡ Smart Download: Video is short ({total_duration}s). Using FULL download mode."
                )

            # 2. If we want > 50% of the video, download FULL.
            elif wanted_duration > (total_duration * 0.5):
                use_full_download = True
                print(
                    f"⚡ Smart Download: Segment > 50% ({wanted_duration}s). Using FULL download mode."
                )
            else:
                print(
                    f"⚡ Smart Download: Specific Segment ({wanted_duration}s). Using PARTIAL download mode."
                )

        else:
            # No range specified = Full Download
            use_full_download = True

        # Configure yt-dlp based on Strategy
        if resolution == "source":
            res_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            res_format = f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best"

        ydl_opts = {
            "format": res_format,
            "outtmpl": f"{self.temp_dir}/%(id)s.%(ext)s",
            "paths": {"home": self.temp_dir, "temp": self.temp_dir},
            "noplaylist": True,
            "quiet": False,
            "no_warnings": True,
            "concurrent_fragment_downloads": 4,
            "buffersize": 1024 * 1024,
            "progress_hooks": [progress_hook],
        }

        if not use_full_download:
            # PARTIAL STRATEGY (Optimization: Disable Re-encoding)
            msg = f"✂️  Downloading Partial Segment: {start_time} to {end_time}"
            print(msg)
            if logger:
                logger.log(msg, "INFO")

            ydl_opts["download_sections"] = [
                {
                    "start_time": start_sec,
                    "end_time": end_sec,
                    "title": "Analysis_Segment",
                }
            ]
            ydl_opts["external_downloader"] = "ffmpeg"
            # CRITICAL OPTIMIZATION: -c copy (No Re-encoding). 10x Faster.
            # Trade-off: Keyframe snap (might be +/- 2s loose).
            ydl_opts["external_downloader_args"] = {
                "ffmpeg_i": ["-ss", str(start_sec), "-to", str(end_sec)],
                "ffmpeg_o": ["-c:v", "copy", "-c:a", "copy"],
            }
            # Ensure we don't force keyframes, as we want 'copy' mode
            ydl_opts["force_keyframes_at_cuts"] = False
        else:
            # FULL STRATEGY
            print("⬇️  Downloading Full Video...")
            # Default behavior is fine

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                title = info.get("title", "Unknown_Video")
                print(f"✅ Download Complete: {filename}")
                return filename, title
        except Exception as e:
            if cancel_event and cancel_event.is_set():
                print(f"🛑 Download Cancelled.")
                return None, None
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

        # Determine project root
        if getattr(sys, "frozen", False):
            self.root_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.root_dir = os.path.dirname(base_dir)

    def transcribe(self, video_path, logger=None):
        """
        Primary transcription method — uses SUBPROCESS ISOLATION by default.

        LESSON #13: CTranslate2's C++ destructor segfaults during CUDA cleanup.
        This is a C-level crash that Python try/except cannot catch.
        Running Whisper in a subprocess lets the OS reclaim GPU memory on
        process exit, completely avoiding the destructor crash.
        """
        return self.transcribe_subprocess(video_path, logger=logger)

    def transcribe_subprocess(self, video_path, logger=None):
        """
        Runs Whisper transcription in a SEPARATE PROCESS to avoid CTranslate2
        CUDA destructor segfault. Results are passed via a temporary JSON file.
        """
        import subprocess
        import json
        import time

        msg = "🎙️  Starting Transcription (Subprocess Isolation Mode)..."
        print(msg)
        if logger:
            logger.log(msg, "INFO")

        # Paths
        worker_script = os.path.join(self.root_dir, "src", "transcribe_worker.py")
        temp_dir = os.path.join(self.root_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        output_json = os.path.join(temp_dir, "transcription_result.json")

        # Clean up any previous result file
        if os.path.exists(output_json):
            os.remove(output_json)

        # Determine Python executable (use venv)
        python_exe = os.path.join(self.root_dir, ".venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            # Fallback to current interpreter
            python_exe = sys.executable

        cmd = [
            python_exe,
            worker_script,
            video_path,
            output_json,
            self.model_size,
        ]

        msg = "🚀 Launching transcription subprocess..."
        print(msg, flush=True)
        if logger:
            logger.log(msg, "INFO")

        start_time = time.time()

        try:
            # Run subprocess — stream stdout/stderr to parent's console
            process = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                encoding="utf-8",
                errors="replace",
            )

            # Stream output in real-time
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(line, flush=True)
                    # Forward interesting logs to the main logger (WebSocket)
                    if logger:
                        # Filter for relevant worker logs to avoid double-printing everything
                        if any(
                            k in line
                            for k in ["[WORKER]", "Processing", "Transcribing", "%"]
                        ):
                            logger.log(line, "INFO")

            # Wait for completion
            return_code = process.wait(timeout=600)

            elapsed = time.time() - start_time

            if return_code != 0:
                # Check for segfault codes or other errors using the same logic as before
                if os.path.exists(output_json):
                    expected_segfault_codes = [3221226505, -1073741819, -11]
                    if return_code in expected_segfault_codes:
                        msg = f"✅ Transcription Subprocess finished (exit code {return_code} suppressed - data saved)."
                        print(msg, flush=True)
                        if logger:
                            logger.log(msg, "INFO")
                    else:
                        msg = f"⚠️ Subprocess connection closed ({return_code}). Checking for results..."
                        print(msg, flush=True)
                else:
                    raise RuntimeError(
                        f"Transcription subprocess failed with exit code {return_code}"
                    )

        except subprocess.TimeoutExpired:
            raise RuntimeError("Transcription subprocess timed out after 10 minutes.")

        # Read results from JSON
        if not os.path.exists(output_json):
            raise RuntimeError(f"Transcription output file not found: {output_json}")

        with open(output_json, "r", encoding="utf-8") as f:
            word_list = json.load(f)

        # Clean up temp JSON
        try:
            os.remove(output_json)
        except Exception:
            pass

        msg = f"✅ Transcription Complete ({len(word_list)} words in {elapsed:.1f}s)"
        print(msg, flush=True)
        if logger:
            logger.log(msg, "INFO")

        # Brief pause to let GPU memory settle after subprocess exit
        time.sleep(1)

        return word_list

    # --- Legacy in-process methods (kept as fallback) ---

    def load_model(self):
        if self.model is None:
            print(
                f"🧠 Loading Whisper Model ({self.model_size}) to {self.device.upper()}..."
            )
            model_cache_dir = os.path.join(self.root_dir, "models", "whisper")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=model_cache_dir,
            )
            msg = f"✅ Model Loaded on {self.device.upper()} (Compute: {self.compute_type})"
            print(msg)

    def transcribe_inprocess(self, video_path, logger=None):
        """Legacy in-process transcription. WARNING: May segfault during cleanup."""
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

        segments, info = self.model.transcribe(
            video_path, beam_size=5, word_timestamps=True, vad_filter=True
        )

        msg = f"   Detected Language: {info.language.upper()} (Probability: {info.language_probability:.2f})"
        print(msg)
        if logger:
            logger.log(msg, "INFO", "CYAN")

        word_list = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    word_data = {
                        "start": word.start,
                        "end": word.end,
                        "word": word.word.strip(),
                    }
                    word_list.append(word_data)
                    print(".", end="", flush=True)

        msg = f"\n✅ Transcription Complete. {len(word_list)} words extracted."
        print(msg)
        if logger:
            logger.log(msg, "INFO")

        return word_list


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
