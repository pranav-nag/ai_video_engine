# Developer Log & Scratchpad

> **Purpose**: Use this file to store temporary drafts, brainstorm ideas, log session outputs, and keep track of decisions. This prevents cluttering the main `PROJECT_MEMORY.md` with ephemeral data.

## Session: 2026-02-15 [Critical Fixes & Theme Upgrade]

### Log
- **User Issue**: "Ollama is NOT running" error blocked AI analysis.
- **Root Cause**: Strict model check for `qwen2.5:7b` failed if only other models were installed.
- **FIXED**: `analyzer.py` now checks for *any* Qwen/Llama/Mistral model as a fallback before forcing a download.
- **User Issue**: Frontend terminal froze during transcription.
- **Root Cause**: `subprocess.run` buffered stdout, preventing real-time updates to the UI WebSocket.
- **FIXED**: Switched to `subprocess.Popen` with `bufsize=1` and line-by-line yielding in `ingest_transcribe.py`.
- **User Issue**: App crashed with `[NO_LOGGER]` or backend SyntaxError.
- **Root Cause 1**: Windows file locking prevented `rename_log_file` from working. Added retry/fallback in `logger.py`.
- **Root Cause 2**: Duplicate `global OLLAMA_MODEL` declaration in `analyzer.py` caused a syntax error. Fixed.
- **Feature**: User requested separation of App Theme (Sidebar) from Video Theme (Captions).
- **Implemented**: Added `Interface Theme Picker` in Sidebar header and moved `Quick Themes` (Video) to a collapsible section.

### Completed
- Ollama Connection Resilience
- Terminal Real-time Sync
- Windows File Lock Handling
- Sidebar Theme Architecture Refactor

## Session: 2026-02-15 [Parity & Cleanup]

### Log
- **WebSocket Stability**: Added 3s auto-reconnect logic in `App.tsx` and upgraded `api.py` to use `lifespan` event handlers.
- **Workflow Optimization**: Created `run.bat` (unified build + start script) and updated root `package.json` with multi-tier build scripts.
- **Project Structure**: Organized AI Agent documentation into the `brain/` folder for better focus.
- **Legacy Cleanup**: Deleted obsolete `.bat` files and archived old planning documents.
- **Content Updates**: Refactored internal naming (e.g., `FletProglog` -> `UIProglog`) to fully decouple from legacy framework references.

### Completed
- WebSocket Auto-Reconnect (Stability)
- Unified Run/Build Command (`run.bat`)
- Documentation Reorganization (`brain/` folder)
- Framework Decoupling (Naming cleanup)

### Next Steps
- Perform deep E2E testing to ensure rendering parity with the original Flet app.

---

## Session: 2026-02-09 [Visual & Viral Upgrade]

### Log
- Analyzed existing documentation structure.
- User approved 4-File System: `USER_PROMPTS.md`, `PLAN.md`, `DEV_LOG.md`, `PROJECT_MEMORY.md`.
- Consolidated `SYSTEM.md` and `PROMPTS.md` into `PROJECT_MEMORY.md`.
- Created `USER_PROMPTS.md` for dedicated input.
- Re-created clean `PLAN.md`.
- **IMPLEMENTED**: Multi-Frame Virality Scoring in `analyzer.py` (Start/Mid/End checks).
- **IMPLEMENTED**: Emoji suggestion request in LLM Prompt.
- **IMPLEMENTED**: New `.ass` Subtitle Renderer in `renderer.py` (Replaced TextClip with FFmpeg burn-in).
- **VERIFIED**: Fixed `moviepy` 2.0 compatibility issues (`subclipped`) and `opencv-python` venv dependency.
- **VERIFIED**: `test_pipeline.py` passed successfully.
- **POLISHED**: Updated `main_ui.py` with Modern Dark Theme and Glassmorphism.
- **DOCUMENTED**: Updated `PROJECT_MEMORY.md` with strict `.venv` usage rules.

### Completed
- Visual Upgrade (Captions)
- Enhanced Virality Scoring
- Smart Cropping (Scene Snap)
- UI Polish (Modern Dark Theme)

### Next Steps
- Verify end-to-end flow with a real long-form video.

---

## Session: 2026-02-09 22:55 [UI Layout \u0026 Crash Fix]

### Log
- Analyzed user-reported issues: UI text cutoff and pipeline crash
- Identified root cause: Duplicate vision analysis code (lines 476-542 in `analyzer.py`)
- **FIXED**: Duration Info now scrollable (60px container with AUTO scroll)
- **FIXED**: Caption Size slider now shows live value display ("Caption Size: 60px")
- **FIXED**: AI & Target tab now scrollable to show all content
- **FIXED**: Removed 67 lines of duplicate vision analysis code from `analyzer.py`
- **IMPROVED**: Enhanced error handling with full traceback logging for debugging
- Crash was caused by redundant vision processing exhausting VRAM/causing exceptions

### Completed
- UI Layout Issues (3 fixes)
- Pipeline Crash Resolution
- Error Logging Enhancement

---

## Session: 2026-02-10 21:05 [Output Quality Overhaul]

### Log
- Analyzed output video via ffprobe: 607x1080, 820kbps video, 127kbps audio, gbrp pixel format
- **ROOT CAUSE**: `resize()` → `resized()` MoviePy 2.x rename; bare `except: pass` hiding the failure
- **FIXED**: Resolution — MoviePy 2.x `resized()` API with error logging
- **FIXED**: Video Bitrate — VBR 26 Mbps / 30M maxrate (Premiere Pro YouTube match)
- **FIXED**: Audio Bitrate — 320kbps AAC
- **FIXED**: Pixel Format — `yuv420p`, `profile:v high`, `level:v 4.2`
- **FIXED**: Face Cropping — Per-frame dynamic crop with interpolation (replaces static averaging)
- **FIXED**: Caption Timing — Gap-free word display (each word → next word start), 50ms pre-buffer
- **FIXED**: Emoji — Removed from ASS text (libass can't render colored Unicode)
- **FIXED**: FPS 24 → 30, CPU fallback upgraded to CRF 18 / slow preset
- **IMPROVED**: Output filenames now include timestamp and clip start time for easy recognition

### Completed
- Output Quality (7 fixes across renderer.py & fast_caption.py)

### Next Steps
- Re-render a test clip and verify via ffprobe + visual check

---

## Session: 2026-02-10 22:30-23:15 [Professional Overhaul - UI/AI/Captions]

### Log
- **PHASE 1 - Core Analysis Fix**: Hardened `analyzer.py` prompt and validation
  - Updated system prompt to strictly enforce min/max duration constraints
  - Added pre-validation check (discard clips outside duration range immediately)
  - Improved scene snapping to validate duration AFTER snap (reject if out of bounds)
  - Changed logic to prefer valid duration over strict scene boundaries
- **PHASE 2 - Caption Engine 2.0**: Refactored `fast_caption.py` for multi-style support
  - Created STYLES dictionary with 4 presets: Hormozi, Minimal, Neon, Boxed
  - Each style defines Fontname, PrimaryColour, OutlineColour, BorderStyle, Outline, Shadow
  - Added position override support (top/center/bottom)
  - Simplified `renderer.py` to delegate all styling to SubtitleGenerator
- **PHASE 3 - VRAM Crash Fix**: Enhanced `ingest_transcribe.py` cleanup
  - Wrapped entire `free_memory()` in try/except to prevent silent crashes
  - Added `torch.cuda.synchronize()` with individual error handling
  - Improved logging for VRAM cleanup status
- **PHASE 4 - UI Bug Fixes**:
  - Removed duplicate "Position" dropdown in Co-Pilot Styles tab
  - Set `page.padding=0` and `page.spacing=0` for edge-to-edge layout
  - Attempted sidebar gap removal (PARTIAL SUCCESS - still some padding issues)

### Completed
- AI Duration Enforcement (analyzer.py)
- Professional Caption Styles (fast_caption.py)
- VRAM Cleanup Safeguards (ingest_transcribe.py)
- UI Duplicate Removal (main_ui.py)

### Known Issues
- **UI Layout**: Top/bottom padding still visible in sidebar despite multiple attempts
- **Transcription Crash**: VRAM cleanup error handling added, but not fully verified
- **Bare except blocks**: Lint warnings in main_ui.py and analyzer.py

### Next Steps for Future Sessions
- Resolve sidebar padding issue (user frustrated with current state)
- Test complete pipeline to verify crash fixes
- Benchmark against competitors (Opus.pro, Klap.app)
---

## Session: 2026-02-11 00:00 [Subprocess Isolation & UX Fixes]

### Log
- **FIXED**: Critical VRAM crash during transcription cleanup.
  - Implemented **Subprocess Isolation**: Whisper now runs in `src/transcribe_worker.py`.
  - Main app is now protected from CTranslate2 C++ destructor segfaults.
  - Simplified `main_ui.py` by removing complex stdout/stderr redirection.
- **FIXED**: Rendering crash caused by missing `time_to_ass` method in `fast_caption.py`.
- **IMPROVED**: AI Analysis UX.
  - Switched Ollama to `stream: True`.
  - Added live token counter and elapsed time display in the progress bar.
- **FIXED**: ETA formatting.
  - Converted raw seconds to `mm:ss` or `hh:mm:ss` in both Cropper and Renderer.
- **VERIFIED**: Checked the pipeline flow; transcription succeeds and data is preserved even if the worker subprocess segfaults on exit.

### Completed
- Transcription Subprocess Isolation
- Rendering Crash Resolution (`time_to_ass`)
- AI Streaming Progress Feedback
- Human-readable ETA Formatting

### Next Steps
- Solve sidebar padding/margin issue.
- Monitor long-form video processing stability with the new subprocess model.

---

## Session: 2026-02-11 00:30 [Content Quality & AI Tuning]

### Log
- **IMPROVED**: Clip Quality Logic.
  - User feedback: "Clips too short (28s) and sentiment analysis generic."
  - **Action**: Increased default duration constraints from 15-60s to **30-60s**.
  - **Action**: Updated UI slider default start value to **30s**.
  - **Action**: Rewrote `analyzer.py` System Prompt to prioritize "Story Mode" (Hook/Payload/Payoff) and "Emotional Resonance" over generic "funny" clips.
- **FIXED**: Alarming Log Messages.
  - User feedback: "Please fix this error" (referring to expected subprocess segfault).
  - **Action**: Updated `ingest_transcribe.py` to catch exit code `3221226505` (Access Violation) and log it as **INFO (Success)** if data is saved.
- **RESTORED**: Accidentally deleted scene detection logic in `analyzer.py` during refactor.

### Completed
- AI Prompt Engineering (Viral/Story Focus)
- Duration Logic Update (30s+ default)
- Log Noise Reduction (Suppressing clean segfaults)

### Next Steps
- **User Verification**: accurate testing of the new prompt logic on a full video.
- **Sentiment Tuning**: If clips are still generic, consider switching to `qwen2.5:14b` or `gemma:9b` (if VRAM permits).


## Session: 2026-02-11 23:55 [Bug Squash & UI Polish]

### Log
- **FIXED**: "Target Length" label used static text "15-60s", mismatching the new default "30-60s". Fixed `main_ui.py` to match.
- **FIXED**: Filename Confusion. Output files were named `Clip1_540s.mp4`. Users interpreted "540s" as duration (9 mins) instead of Start Time.
  - **Action**: Changed format to `Clip1_Start09m00s_Dur45s.mp4`. Explicit and unambiguous.
- **ADDED**: Content Type Selection in UI (Auto / Podcast / Solo).
  - Wired `content_type` dropdown from `main_ui.py` -> `run_ai_pipeline` -> `analyzer.py`.
- **DEBUGGING**: Caption Size Bug.
  - User reports setting 80px but getting default size.
  - Code review shows valid logic in `renderer.py` and `fast_caption.py`.
  - **Action**: Added INFO logging to `renderer.py` to trace `font_size` and `style_name`.
  - Waiting for user test to verify if renderer receives correct value.

### Completed
- UI Label Fix (Target Length)
- Filename Clarity (Start vs Duration)
- Content Type UI Integration
- Caption Size Logging (Debug)

### Next Steps
- Verify Caption Size log output from user.
- Plan B-Roll Integration (Feature Request).



---

## Session: 2026-02-13 22:00 [UI Polish & Memory Optimization]

### Log
- **Analysis**: Conducted deep review of architecture (`ANALYSIS.md`).
- **FIXED**: UI Sidebar Padding. Removed global `page.padding` and `page.spacing` in `main_ui.py`.
- **FIXED**: Caption Size Slider. Added missing `on_change` event handler in `main_ui.py`.
- **OPTIMIZED**: Implemented **Sequential Model Loading** in `analyzer.py`.
  - Added `unload_model()` to force Ollama to free VRAM (`keep_alive=0`).
  - Text model (`qwen2.5`) unloads before Vision model loads.
  - Vision model (`minicpm-v`) unloads after analysis.
- **OPTIMIZED**: Video I/O. rewritten `analyzer.py` to open `cv2.VideoCapture` **once** per batch instead of 3x per clip.
- **CHANGED**: Switched default Vision Model to `minicpm-v` (8B, high efficiency) in `vision_analyzer.py`.

### Completed
- UI Padding Bugs
- Caption Size UI Feedback
- Memory Management (Ollama Unloading)
- Model Selection (Standardized on MiniCPM-V)

- Verify B-Roll integration plan.
- Ensure `analyzer.py` handles auto-pull of modern models (User Requirement).

---

## Session: 2026-02-13 23:45 [Intelligence Overhaul & Smart Downloads]

### Log
- **Analysis**: User reported "0 clips found" due to strict duration constraints, and "unknown decoder 'copy'" on partial downloads.
- **FIXED**: `yt-dlp` Argument Syntax. Moved `-c copy` to `ffmpeg_o` (output args) to fix download error.
- **IMPLEMENTED**: **Smart Semantic Snapping** (`snap_to_word_boundary`).
  - Analyzer now sees exact word-level timestamps.
  - Snaps cut points to nearest sentence ending (`.`, `?`, `!`).
  - Extends clips slightly over limit if needed to finish a sentence.
- **IMPLEMENTED**: **Context Expansion** (`expand_context`).
  - If a clip is too short (<30s), Python automatically adds the previous/next sentences to reach target duration.
  - "Rescues" short viral quotes instead of deleting them.
- **IMPLEMENTED**: **Series Splitting**.
  - If a clip is too long (e.g. 2 mins), it is split into Part 1, Part 2, etc. (snapped to sentences).
- **CHANGED**: **Content First Strategy**.
  - Removed "STRICT DURATION CONSTRAINT" from LLM System Prompt.
  - LLM now focuses purely on "Hooks" and "Payoffs". Python handles the timing.

### Completed
- Smart Download Strategy (Fix)
- Semantic Snapping (No mid-sentence cuts)
- Context Expansion (Rescue short clips)
- Series Splitting (Handle long stories)


---

## Session: 2026-02-14 [Architecture Shift: Electron Migration]

### Log
- **Decision**: User requested a "Modern App" structure, rejecting the Flet UI limits and Web Browser approach.
- **Action**: Planning complete migration to **Electron + React + FastAPI**.
- **Rationale**:
    - **Electron**: Provides native window management (no browser tabs).
    - **React**: Enables "Premium" UI components (Shadcn/Tailwind), visual caption previews, and smart color pickers.
    - **FastAPI**: Wraps existing Python logic (`src/`) into a high-performance local API.
- **Constraints**:
    - **Strict VENV**: Electron must spawn `python.exe` from `.venv` only.
    - **Performance**: Zero-lag communication via WebSockets/AsyncIO.
    - **Memory**: Optimized process management (kill Python on exit).

### Completed
- Scaffolding (Electron/React/FastAPI)
- Backend Implementation (api.py + WebSockets)
- Frontend Implementation (Sidebar, Terminal, Visual Composer)
- End-to-End "Hello World" Proof of Concept

---

## Session: 2026-02-14 21:30 [Polish & Packaging]

### Log
- **GOAL**: Turn the "Hello World" scaffold into a production-ready app.
- **Frontend Polish**:
    - Ported `Sidebar.tsx` to include all Flet features: `Resolution` (9:16, 16:9, 1:1), `Focus Mode` (Center/Auto/Left/Right), `Content Type`.
    - Fixed syntax errors in `Sidebar.tsx` (duplicate closing tags).
- **Backend Cleanup**:
    - Implemented `cleanup_temp_files` in `api.py` shutdown event to prevent disk bloat.
    - Added `try/except` blocks around cleanup to ensure graceful exit.
- **Electron Build Config**:
    - Configured `electron-builder` in `package.json` to package:
        - `electron/main.js` (Main Process)
        - `backend/` (Python Code)
        - `frontend/dist/` (React UI)
        - `.venv/` (Python Environment - **CRITICAL**)
- **Path Resolution Fix**:
    - `main.js`: detected `process.env.NODE_ENV` to switch between `../.venv` (Dev) and `process.resourcesPath/.venv` (Prod).
  
### Completed
- Feature Parity (Frontend controls match Flet)
- Graceful Shutdown (Cleanup)
- Production Build Configuration
- Path Resolution Logic (Dev vs Prod)

### Next Steps
- User to run `npm run dist` and test the final `.exe`.

---

## Session: 2026-02-14 22:00 [Size Optimization]

### Log
- **Analysis**: Project size hit 27GB. Breakdown:
    - `cache/` (HuggingFace): **13.16 GB** -> DELETE (Redundant)
    - `electron/dist/` (Build Artifacts): **5.89 GB** -> DELETE (Regenerate)
    - `.venv/` (Python Env): **5.64 GB** -> KEEP (Critical)
    - `models/` (Active Whisper): **1.51 GB** -> KEEP (Critical)
- **Goal**: Clear ~19GB of redundant data.
- **Action**: Deleted `cache/` and `electron/dist/` (User Approved).
- **Result**: ~19GB Free Space Reclaimed. Project now ~7GB (mostly `.venv` + `models`).
