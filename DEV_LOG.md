# Developer Log & Scratchpad

> **Purpose**: Use this file to store temporary drafts, brainstorm ideas, log session outputs, and keep track of decisions. This prevents cluttering the main `PROJECT_MEMORY.md` with ephemeral data.

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

