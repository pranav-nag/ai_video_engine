# AI Video Engine - Project Memory & Context

> **Purpose**: This document is the **Single Source of Truth** for AI Agents working on this project. It defines the architecture, constraints, and operational rules.

---

## 🛑 CRITICAL OPERATIONAL RULES (DO NOT IGNORE)

### 1. Environment & Safety
> [!CRITICAL]
> **VIRTUAL ENVIRONMENT IS MANDATORY**
> **Current Path**: `E:\AI_Video_Engine\.venv\Scripts\python.exe`
>
> **YOU MUST ALWAYS USE THE VENV FOR ALL COMMANDS.**
> - ❌ `python script.py` (WRONG)
> - ❌ `pip install package` (WRONG)
> - ✅ `./.venv/Scripts/python script.py` (CORRECT)
> - ✅ `./.venv/Scripts/python -m pip install package` (CORRECT)
>
> **FAILURE TO DO THIS WILL BREAK THE SYSTEM.**
  
### 2. System Dependencies
- **Ollama**: This is a **SYSTEM APPLICATION**, not a Python package. 
  - **DO NOT** attempt to pip install it.
  - **DO NOT** delete it. 
  - It must be running in the background for analysis to work.
- **ImageMagick**: Located at `assets/ImageMagick/convert.exe`.

### 3. Documentation Protocol
- **Start of Session**: Read `PROJECT_MEMORY.md` (this file) and `USER_PROMPTS.md`.
- **Planning**: Update `PLAN.md` before writing code.
- **Execution**: Log major decisions in `DEV_LOG.md`.
- **End of Session**: Update this file with new learnings (Section 7).

---

## 1. Project Architecture

**Goal**: automated viral short-form video generator (TikTok/Shorts) based on transcript and visual analysis.

### Core Pipeline (`src/`)
| Module | Function | Key Models/Tech |
|:---|:---|:---|
| **`ingest_transcribe.py`** | Downloads video & Generates timestamps | `yt-dlp` (Multi-thread), `faster-whisper large-v3-turbo` |
| **`analyzer.py`** | Finds viral hooks & scene scenes | `qwen2.5:7b` (Ollama), `SceneDetector` (PySceneDetect) |
| **`vision_analyzer.py`** | Hybrid Visual Scoring | `llava:7b` (Ollama) - Start/Mid/End frame analysis |
| **`cropper.py`** | 9:16 Smart Cropping | `MediaPipe` (Face Mesh), Scene-Aware Smoothing |
| **`fast_caption.py`** | **[NEW]** Subtitle Generation | Generates `.ass` file with Karaoke & Pop Animations |
| **`renderer.py`** | Final Video Composition | `FFmpeg` (burning .ass), `NVENC` (Hardware Accel) |
| **`main_ui.py`** | Desktop GUI | `Flet` (Modern Dark Theme) |

### File Structure
```
E:\AI_Video_Engine\
├── src/                # Source Code
├── output/             # Final MP4s
├── temp/               # Interim files (cleared often)
├── logs/               # Execution logs
├── assets/             # Binary dependencies (ImageMagick)
└── .env                # Config (Ollama URL, Models)
```

---

## 2. Hardware Constraints & Configuration

**System**: Ryzen 7 7435HS | **RTX 4060 (8GB VRAM)** | 24GB RAM

### Optimization Strategy (8GB VRAM)
- **Sequential Loading**: We load one model at a time (Whisper -> Release -> Ollama -> Release).
- **Quantization**: Use INT8/FP16 where possible.
- **Rendering**: Direct `h264_nvenc` encoding via FFmpeg is prioritized over generic MoviePy write modes.

---

## 3. Configuration & Constants

### `.env`
```bash
OLLAMA_BASE_URL=http://localhost:11434
HF_HOME=E:/AI_Video_Engine/models
```

### Models (Updated 2026-02-09)
- **LLM**: `qwen2.5:7b` (Best logic/size ratio)
- **Vision**: `llava:7b` (Hybrid scoring)
- **Audio**: `faster-whisper large-v3-turbo` (Speed favored)

---

## 4. Current State (Pro Upgrade - v2.5)

### ✅ Working Features
- **Dynamic Captions**: `.ass` based rendering with "Pop" animations and multi-style support.
- **Subprocess Transcription**: Whisper is isolated to prevent CUDA cleanup segfaults (safe on 8GB VRAM).
- **Streaming AI Analysis**: Real-time token progress and timing feedback during Ollama analysis.
- **Smart Logic**: Tuned "Story Mode" prompt (Hook/Payload/Payoff) + strict 30-60s duration + Scene boundary injection.
- **Performance**: Subprocess model ensures stability even when CTranslate2 crashes on exit.
- **Safe Logging**: Harmless shutdown segfaults (Exit 0xC0000005) are automatically suppressed and logged as success.
- **Professional Output**: 26 Mbps VBR video, 320 kbps AAC, 1080x1920, h264_nvenc acceleration.

- **Human-readable ETA**: All progress displays use `mm:ss` format.


### ⚠️ Known Issues / "Gotchas"
- **Ollama Connection**: If `ollama` command fails, ensure the app is running in system tray.
- **Unicode Support**: `.ass` files need escaped backslashes (`\\N`) for newlines.
- **Flet Case Sensitivity**: Use `ft.colors.TRANSPARENT` (Uppercase), not lowercase.

---

## 5. Development Cheat Sheet

### Run the App
```powershell
./.venv/Scripts/python src/main_ui.py
```

### Debugging Tools
```powershell
# Check Models
ollama list

# Test Subtitles
./.venv/Scripts/python test_fast_caption.py
```

### Adding Requirements
**ALWAYS** add to requirements.txt if installing new packages.
```powershell
./.venv/Scripts/pip freeze > requirements.txt
```

---

## 6. Hall of Shame (Lessons Learned)

1. **System vs Venv**: Deleted Ollama from C: thinking it was a local package. **Never delete system apps.**
2. **Infinite Loops**: Legacy `TextClip` loop in MoviePy caused memory leaks. Switched to `ffmpeg` filters.
3. **Ghost Cropping**: Smoothing must reset (`alpha=1.0`) at scene boundaries to prevent face tracking from "sliding" across the screen.
4. **Flet Thread-Safety Crash (2026-02-10)**: Calling `page.update()` from background threads during CUDA/torch operations crashes Flet. **FIX**: The `StreamToLogger` class in `main_ui.py` must NEVER call `page.update()` from threads. Use `sys.__stdout__` for terminal output and rely on ListView's `auto_scroll=True`.
5. **VRAM Cleanup Crash (2026-02-10)**: Explicitly deleting the model (`del self.model`) or calling `torch.cuda.synchronize()` during cleanup caused crashes. **FIX**: Just set `self.model = None`, call `gc.collect()`, and skip synchronization. UPDATE (2026-02-10 23:00): Wrapping entire cleanup in try/except prevents silent crashes. UPDATE (2026-02-10 23:30): `del self.model` triggers CTranslate2's C++ destructor which performs a raw CUDA free that can segfault — **NEVER use `del`** on GPU model objects.
6. **Cropper Type Error**: Scene detection returns dicts (`{'start': ...}`), not floats. **FIX**: Updated `cropper.py` to extract `start` key.
7. **MoviePy 2.x Silent Failure (2026-02-10)**: `clip.resize()` was renamed to `resized()` in MoviePy 2.0. A bare `except: pass` hid the error, causing output at 607×1080 instead of 1080×1920 with 820kbps bitrate. **FIX**: Use `resized()`, never use bare `except: pass`. Always log errors.
8. **Static Crop Averaging (2026-02-10)**: Averaging all face positions into one crop offset meant the speaker got cut in half when they moved. **FIX**: Per-frame dynamic crop with interpolation from `crop_map`.
9. **FPS Force (2026-02-10)**: Forcing 30fps on 23.976fps source caused audio/video/subtitle desync. **FIX**: Removed `fps=30` parameter, now using `clip.fps` from source.
10. **AI Duration Violation (2026-02-10)**: LLM would output clips < min_sec or > max_sec, and scene snapping could push valid clips out of range. **FIX**: Added pre-validation (discard invalid before snap), post-snap validation (reject if snap breaks duration), and hardened prompt.
11. **Flet Layout Expand Bug (2026-02-10 23:15)**: Setting `expand=True` on settings_tabs container caused it to consume ALL vertical space, hiding buttons and controls. **FIX**: Use fixed `height=520` instead of `expand=True` for nested containers in a Column.
12. **Stdout Redirect During CUDA Cleanup (2026-02-10 23:30)**: When `sys.stdout` is redirected to `StreamToLogger`, the Whisper model's C++ destructor writes to stdout/stderr during garbage collection. If `StreamToLogger` tries to call Flet controls from a background thread at that moment, the app crashes silently (exit code != 0). **FIX**: Restore `sys.__stdout__` before transcription, initialize `words = None` before try block, and add explicit error handling that restores streams before re-raising. Also add a 2-second GPU stabilization delay before starting Ollama analysis.
13. **CTranslate2 Segfault is Uncatchable (2026-02-10 23:45)**: The CTranslate2 C++ destructor segfaults during CUDA cleanup regardless of whether you use `del`, `None`, or any Python-level workaround. This is a C-level access violation that `try/except` **cannot catch**. **FIX**: Run Whisper transcription in a **subprocess** (`transcribe_worker.py`). When the subprocess exits, the OS reclaims all GPU memory. Even if the destructor segfaults, only the subprocess dies. The JSON result file is written *before* the crash, so data is preserved.
14. **Missing `time_to_ass` Method (2026-02-11 00:00)**: `SubtitleGenerator` in `fast_caption.py` called `self.time_to_ass()` but the method was never defined — instant crash at rendering. **FIX**: Added the method that converts float seconds to ASS timecode `H:MM:SS.CC`. Also switched Ollama analysis from blocking `stream: False` to `stream: True` with live token progress feedback.
15. **Suppressing 'Safe' Segfaults (2026-02-11 00:15)**: The CTranslate2 library has a known bug where its C++ destructor segfaults (Exit Code 0xC0000005) when freeing CUDA memory at process exit. This is **unfixable** from Python as it happens after the global interpreter shuts down. **STRATEGY**: Since the transcription data is already saved to disk, we treat this specific exit code as "Success" and suppress the warning log. This is a permanent limitation of the current `faster-whisper` backend version.
 - ~~**MoviePy 2.0 Compatibility**: `subclip` removed in v2.0~~ — Already using `subclipped`. Resolved.
 
---

> **Agent Note**: If you fix a new bug, add it to Section 6. If you change architecture, update Section 1.
