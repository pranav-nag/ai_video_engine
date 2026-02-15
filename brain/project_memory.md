# AI Video Engine: Project Memory & Internal Technical Specs

> **Status**: Active Development
> **OS**: Windows 11 (Optimized for NVIDIA RTX 4060)
> **Stack**: Electron + React (Frontend) | Python FastAPI (Backend) | FFmpeg + Ollama (Core)

This is the **Definitive Source of Truth** for the AI Video Engine. It documents the core architecture, hardware-specific optimizations, rendering protocols, and complex algorithms in extreme depth.

---

## 🛑 CRITICAL OPERATIONAL RULES

### 1. Environment & Safety
- **VIRTUAL ENVIRONMENT IS MANDATORY**: Always use `E:\AI_Video_Engine\.venv\Scripts\python.exe`. Never run bare `python`.
- **ARCHITECTURE ENFORCEMENT**: The project is **Electron + React + Python (FastAPI)**. Do not introduce other frameworks like Flet or Tkinter.
- **PROCESS ISOLATION**: Heavy AI tasks (Whisper) **MUST** run in a separate subprocess to prevent C++ memory crashes (Exit 3221226505).

### 2. File System & Paths
- **Electron Production**: In built mode, python resources are in `process.resourcesPath`.
- **FFmpeg Paths**: Windows paths passed to FFmpeg filters (like subtitles) **MUST** escape the drive colon (e.g., `E\:/temp/file.ass`).
- **Temp Files**: Always use `E:\AI_Video_Engine\temp` (or project root `temp`) to avoid C: drive permission/space issues.

- **Video Generation**
  - **Resolution**: 1080x1920 (9:16 Vertical)
  - **Layout Engine**: Auto-detects Solo (Crop) vs Podcast (Split Screen) using `src/layout_engine.py` (Opus-style).
  - **Captions**:
    - **Engine**: ASS (Advanced Substation Alpha) via `fast_caption.py`
    - **Visuals**: "Super-Captions" with colored Power Words and Emojis (Phase 6)
    - **Pipeline**: Transcript -> `caption_enhancer.py` (Color/Emoji Tagging) -> ASS Render
  - **Hardware**: NVENC (RTX 4060) with CPU fallback
  - **Audio**: 
    - Background music ducking (-20dB)
    - **Polish**: Auto de-clicking (0.05s fade in/out) to prevent cuts sounding rough.
  - **Visuals**:
    - **Digital Zooms**: Auto-punch in (1.15x) for static clips > 5s.
    - **Smart B-Roll**:
        -   **Trigger**: Keyword match (Power Words) or long face-less gaps.
        -   **Source**: Local `assets/b_roll` + Auto-Download via Pexels/Fallback URLs.
    - **Interactive Editor** (Phase 10):
        -   **Global Toggles**: User can disable B-Roll or Split-Screen via UI.
        -   **Edit Modal**: Visual "Title Safe" overlay on video player.
        -   **Rerender**: Backend endpoint `/rerender_clip` ready for logic (Mocked).
        -   **Status**: Verified Frontend Build & Backend Syntax. Config priority fixed.
- **Filesystem**: 
  - `temp/` for intermediate assets
  - `brain/` for documentation artifacts
- **Process Priority**: `BELOW_NORMAL_PRIORITY_CLASS` (via `psutil`) for ffmpeg/rendering to prevent UI lag.
- **Job Management**: SQLite-backed `JobManager` for persistence, recovery, and state tracking (Pending, Processing, Completed, Failed, Cancelled).
- **Fonts**: Automated `download_fonts.py` (with redirect/user-agent support) and `check_fonts.py` verification.

### IPC Messages (Electron <-> Python)
- `progress_rich`: `{ "phase": "Scanning...", "phase_progress": 0.5, "text": "..." }`
- `CLIP_READY`: `path` | `title` | `thumbnail_path` | `score`
- `log`: `message` | `level` (INFO, ERROR, WARN, SUCCESS)

### 3. System Dependencies
- **Ollama**: Must be installed as a system service. The app attempts to auto-start it if connection fails.
- **FFmpeg**: Must be in PATH or bundled. Used for all video rendering and smart partial downloads.

---

## 🏗️ 1. System Architecture

The application uses a **Tri-Process Architecture** to ensure UI responsiveness while performing heavy AI compute.

### A. Frontend (Electron + React)
- **Role**: User Interface, Configuration, Real-time Logs, Clip Preview.
- **Tech**: React 18, Vite, TailwindCSS, Shadcn UI.
- **Entry Point**: `electron/main.js` spawns the Python backend in a visible console window (for debugging/transparency).
- **Communication**: Connects to Backend via WebSocket (`ws://127.0.0.1:8000/ws`).
- **State**: `App.tsx` manages global state (Config, Logs, Progress) and handles WebSocket events.

### B. Backend (Python FastAPI)
- **Role**: Orchestration, API interactions, Process Management.
- **Entry Point**: `backend/api.py` (served by Uvicorn).
- **Concurrency**:
    - **Worker Thread**: `src/pipeline.py` runs in a `threading.Thread`, managed by `src/job_manager.py`.
- **IPC**: Broadcasts logs and progress (with ETA) to Frontend via `WebSocketManager`.

### C. Compute Engines (Subprocesses / External)
- **Whisper**: Runs in a fully isolated `subprocess` (`transcribe_worker.py`) to handle CTranslate2/CUDA memory safety.
- **Ollama**: External HTTP service (`localhost:11434`) for LLM and Vision tasks.
- **FFmpeg**: External process for rendering and filtering.

---

## 🧠 2. Deep Dive: Core AI Engines

### A. Ingestion Engine (`src/ingest_transcribe.py`)
**Smart Download Strategy**:
1.  **Short Videos (<15m)**: Downloads FULL video (safer, less fragmentation).
2.  **Long Videos**:
    -   If >50% of duration is requested -> FULL download.
    -   If specific segment requested -> **PARTIAL download** using `yt-dlp` + `ffmpeg` external downloader (`-ss`, `-to`, `-c copy`).
    -   *Benefit*: 10x faster for picking a 1-minute clip from a 3-hour podcast.

### B. Transcription Engine (`src/transcribe_worker.py`)
-   **Model**: `faster-whisper` (CTranslate2 backend).
-   **Isolation**: The main app spawns a separate python process for transcription.
    -   *Reason*: CTranslate2's C++ destructor often segfaults when releasing CUDA memory alongside other libraries (Torch/TensorFlow). Process termination guarantees OS-level memory reclamation.
-   **Output**: Word-level timestamps saved to a temporary JSON file.

### C. Analysis Engine (`src/analyzer.py`)
**Viral Scoring Algorithm** (LLM-based):
-   **Prompt Engineering**: Content-aware prompts (Podcast vs. Solo).
-   **Scoring (0-100)**:
    -   **+20**: Hook Potential (Strong opening).
    -   **+15**: Emotional Resonance (Laughter, Anger, Shock).
    -   **+10**: Podcast Dynamics (Debate, Interaction).
    -   **-15**: Dry monologue, filler, or incomplete thoughts.
-   **Semantic Snapping**:
    ```python
    # Algorithm to prevent mid-sentence cuts:
    # 1. Look ahead 15 words for [. ! ?]
    # 2. If found within buffer (Max Duration + 5s), EXTEND clip.
    # 3. Else, look back 10 words and TRIM clip.
    ```
-   **Context Expansion**: If a viral moment is too short (<30s), the engine recursively prepends/appends surrounding sentences until minimum duration is met.

### D. Vision Engine (`src/cropper.py`)
**Smart Face Tracking**:
-   **Library**: MediaPipe Face Detection (Short Range).
-   **Logic**:
    1.  **Scoring**: Faces are scored by Area * Position Weight (Center/Left/Right preference).
    2.  **Stickiness**: A "Stickiness Bonus" is applied to the face detected in the *previous* frame to prevent jumping between speakers in a single shot.
    3.  **Scene Detection**: Uses `src/scene_detect.py` (PySceneDetect) to identify cuts.
    4.  **Smoothing**:
        -   **Within Scene**: Exponential Smoothing (Alpha 0.2) for cinematic camera movement.
        -   **At Scene Cut**: Instant Snap (Alpha 1.0) to jump immediately to the new speaker.

---

## 🎬 3. Rendering Engine (`src/renderer.py`)

### FFmpeg Pipeline
The engine constructs a complex filter chain to achieve professional results:

1.  **Dynamic Crop**: `MoviePy` transforms the frame based on `cropper.py` coordinates (9:16 aspect ratio).
2.  **B-Roll Overlay**:
    -   If no face is detected for >2.0s, the engine overlays random B-Roll from `assets/b_roll`.
    -   This hides awkward camera panning on empty chairs.
3.  **Subtitle Burn-in**:
    -   Generates an `.ass` (Advanced SubStation Alpha) file.
    -   Uses FFmpeg `subtitles` filter (HARD BURN) for maximum compatibility.
4.  **Encoding & Modernization**: 
    -   Standardized on **MoviePy V2.0+** using the `with_effects` syntax for all transformations.
    -   **Codec**: `h264_nvenc` (NVIDIA Hardware Acceleration).
    -   **Bitrate**: 26Mbps VBR (Matches Premiere Pro YouTube High Quality).
    -   **Audio**: AAC 320kbps.

### Caption Styling (`src/fast_caption.py`)
Directly generates ASS tags for high-performance rendering:
-   **Karaoke**: `{\k<duration>}` tags for word-level timing.
-   **Active Word**: `{\c&H00FF00&}` (Green highlight).
-   **Pop Animation**: `{\t(0,100,\fscx115\fscy115)}` (Scale up 115% at word start).
-   **Layers**: Background boxes are drawn as a separate border layer behind the text.

---

## 📡 4. Communication Protocol (WebSocket)

**Endpoint**: `/ws`

### Server -> Client Events
| Type | Payload | Description |
| :--- | :--- | :--- |
| `log` | `{"text": str, "color": str}` | Console log line to display in Terminal. |
| `progress` | `{"progress": float}` | Global progress bar update (0.0 to 1.0). |
| `clip_ready`| `{"path": str, "title": str}` | Notification that a clip has finished rendering. |
| `status` | `{"state": "success"\|"error"\|"cancelled"}` | Pipeline completion status. |

### Client -> Server (HTTP POST)
-   `/process`: Starts the `run_ai_pipeline` thread.
-   `/cancel`: Sets the global `threading.Event` to stop all operations.
-   `/metadata`: Fetches video title/duration via `yt-dlp` (fast check).
-   `/status/ai`: Health check for Ollama.

---

## ⚰️ 5. Hall of Shame (Lessons Learned)

*Technical pitfalls encountered and solved.*

1.  **System vs Venv**: Never delete system-level apps (Ollama) thinking they are Python packages.
2.  **Infinite Loops**: Legacy MoviePy `TextClip` loop caused memory leaks. **Solution**: Moved to FFmpeg filters.
3.  **Ghost Cropping**: Smoothing must reset at scene boundaries. **Solution**: `scene_detect.py` integration.
4.  **Flet Thread-Safety**: Background threads interacting with UI caused crashes. **Solution**: Decoupled Websocket architecture.
5.  **VRAM Cleanup Crash**: `del model` triggers segfaults in CTranslate2. **Solution**: Subprocess isolation.
6.  **MoviePy 2.x**: Major breaking changes (`clip.resize` -> `clip.resized`).
7.  **FPS Desync**: Forcing 30fps on 23.97fps sources breaks audio sync. **Solution**: Always respect source FPS.
8.  **Stdout Redirect**: Redirecting C++ stdout crashes Python on Windows.
9.  **FFmpeg Path Escaping**: `subtitles='E\:/path'` is required on Windows.
10. **Unicode Console**: Windows needs `PYTHONIOENCODING=utf-8` for emoji logs.

---

## 🔮 6. Future Roadmap
-   **Opus-style Sticky Preview**: React components mimicking the rendered output in real-time.
-   **Auto-Upload**: Integration with YouTube/TikTok APIs.
-   **Local Whisper V3**: Transition to `large-v3` optimized via TensorRT.
