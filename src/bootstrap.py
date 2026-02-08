import os
import sys
import shutil
import time
import webbrowser
from pathlib import Path
import flet as ft

# --- PATH SETUP ---
# Detect if frozen (PyInstaller) or script
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).parent
    BASE_DIR = EXE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Define portable paths
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
WHISPER_MODELS_DIR = MODELS_DIR / "whisper"


def print_status(message):
    print(f"[BOOTSTRAP] {message}")


def ensure_directories():
    """Ensure all critical directories exist."""
    dirs_to_check = [LOGS_DIR, TEMP_DIR, OUTPUT_DIR, MODELS_DIR, WHISPER_MODELS_DIR]

    for directory in dirs_to_check:
        if not directory.exists():
            print_status(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            # print_status(f"Verified directory: {directory}")
            pass


def check_dependencies():
    """Check if critical dependencies like ffmpeg are available."""
    if shutil.which("ffmpeg") is None:
        print_status("⚠️  WARNING: 'ffmpeg' not found in PATH.")
        print_status("    The app needs FFmpeg to process videos.")
        print_status("    Please install it from: https://ffmpeg.org/download.html")
        time.sleep(2)
    else:
        print_status("✅ FFmpeg found.")


def check_ollama():
    """Check if Ollama is installed and running."""
    if shutil.which("ollama") is None:
        print_status("⚠️  WARNING: 'ollama' not found in PATH.")
        print_status("    The AI features (Llama 3.2) require Ollama.")
        print_status("    Opening download page...")
        try:
            webbrowser.open("https://ollama.com/download")
        except:
            pass
        time.sleep(2)
    else:
        print_status("✅ Ollama found.")


def check_and_download_model():
    """
    Check if Whisper model exists. If not, use faster_whisper to download it.
    This ensures portability (no manual copy needed).
    """
    # Check if folder is empty
    if not WHISPER_MODELS_DIR.exists() or not any(WHISPER_MODELS_DIR.iterdir()):
        print_status("⬇️  Whisper Model missing. Downloading 'medium' model now...")
        print_status("    (This may take a few minutes depending on internet speed)")

        try:
            from faster_whisper import WhisperModel

            # This triggers the download to the specified root
            # We load it lightly (cpu, int8) just to trigger download
            model = WhisperModel(
                "medium",
                device="cpu",
                compute_type="int8",
                download_root=str(WHISPER_MODELS_DIR),
            )

            print_status("✅ Model downloaded successfully.")

            # Cleanup to free memory for the main app
            del model
            import gc

            gc.collect()

        except Exception as e:
            print_status(f"❌ Error downloading model: {e}")
            input("Press Enter to continue (App may crash without model)...")
    else:
        print_status("✅ Whisper Model found.")


def start_app():
    """Import and run the main app."""
    print_status("🚀 Launching AI Video Engine UI...")
    try:
        # Important: Import inside function to avoid early init issues
        from src.main_ui import main

        ft.app(target=main)
    except ImportError as e:
        print_status(f"CRITICAL ERROR: Could not import main_ui: {e}")
        input("Press Enter to exit...")
    except Exception as e:
        print_status(f"CRITICAL ERROR running app: {e}")
        import traceback

        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    print("==================================================")
    print("        AI VIDEO ENGINE - PRO SETUP")
    print("==================================================")

    ensure_directories()
    check_dependencies()
    check_ollama()
    check_and_download_model()

    print("\nInitialization complete.\n")
    time.sleep(1)

    start_app()
