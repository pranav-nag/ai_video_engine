# Project Roadmap & Active Strategy

> **Purpose**: This file tracks **WHAT** needs to be done next.
> **Rule**: When a task is completed, move it to `PROJECT_MEMORY.md` (History) and delete it from here.

## 🚧 ACTIVE TASKS (High Priority)

### UI Polish (URGENT)
- [x] **Sidebar Layout**: Fix top/bottom padding/margin gaps in sidebar
    - User wants true edge-to-edge layout (zero gaps at window borders)
    - **FIXED**: Removed global `page.padding` and `page.spacing`.
- [x] **Responsive Layout**: Ensure all controls visible at different window sizes
    - Verified with new layout logic.

### Optimization (2026-02-13)
- [x] **Memory Architecture**: Implemented Sequential Loading (`unload_model`).
- [x] **Model Upgrade**: Standardized on `minicpm-v` for vision.
- [x] **I/O Speed**: Optimized `analyzer.py` video capture loop.
- [x] **Auto-Pull Models**: Implement automatic `ollama pull` in `analyzer.py` if model is missing. (User Requirement)
  - **Done**: `ensure_ollama_running()` handles auto-pull.

### Architecture Upgrade: Electron Migration (High Priority)
- [x] **Scaffolding**: Initialize React, FastAPI, Electron projects.
- [x] **Backend Implementation**: Create `api.py` and WebSocket manager.
- [x] **Frontend Implementation**: Build Modern UI with Sidebar, Terminal, Visual Composer.
- [x] **Packaging**: Verify `.venv` usage and build standalone `.exe`.

### Housekeeping & Cleanup (completed)
- [x] **Archive Legacy**: Move Flet code to `legacy/`.
- [x] **Disk Optimization**: Clear `cache/` and `dist/` folders (Saved 19GB).
- [x] **Standards**: Enforce Prettier and Gitignore.

### Testing & Quality
- [ ] **End-to-End Test**: Verify full workflow in packaged app.
- [ ] **Performance Benchmarking**: Ensure zero lag.

---

## ✅ RECENTLY COMPLETED (2026-02-15)

### Sidebar & Theme Upgrade
- [x] **Theme Separation**: Split "App Interface Theme" from "Video Caption Theme".
- [x] **New Controls**: Added Interface Theme Picker (Popover) and collapsible Quick Themes.
- [x] **Default Settings**: Updated AI Strategy to "Podcast" + "Auto Face" by default.

### Critical Fixes
- [x] **Ollama Connection**: Fixed "Ollama is NOT running" error with auto-fallback to available models.
- [x] **Terminal Sync**: Fixed frontend terminal freezing by switching `subprocess.run` to `Popen` with real-time stdout piping.
- [x] **Logger Stability**: Fixed `[NO_LOGGER]` crash on Windows file locks (retry logic).
- [x] **Backend Crash**: Resolved `SyntaxError` (duplicate global) in `analyzer.py`.

### Content Quality (Refined)
- [x] **New Prompting Strategy**: Tuned LLM to look for "Story Arcs" and "Emotional Hooks" (vs just "funny").
- [x] **Duration Enforcement**: Increased default minimum from 15s to **30s** (UI + Logic) to prevent too-short clips.
- [x] **Log Hygiene**: Suppressed "Harmless Segfault" warnings (Exit 3221226505) to prevent user panic.

### Stability & Crash Fixes
- [x] **Subprocess Transcription**: Isolated Whisper to a worker script to prevent C++ destructor segfaults.
- [x] **Rendering Crash**: Added missing `time_to_ass` method to `fast_caption.py`.

### UX & Progress
- [x] **AI Streaming**: Switched Ollama to streaming mode with live token/time feedback.
- [x] **ETA Formatting**: Converted all raw second displays to `mm:ss` or `hh:mm:ss`.
- [x] **Model Verification**: Confirmed `qwen2.5:7b` for best quality on RTX 4060.


### Previous: Caption Engine 2.0 (2026-02-10)
- [x] **Dynamic Karaoke Captions**: Refactored `renderer.py` to use `.ass` subtitles.
- [x] **Style Presets**: Implemented 4 professional styles.

### UX & Polish (2026-02-11)
- [x] **Filename Clarity**: Changed output to `ClipX_Start09m00s_Dur45s.mp4`.
- [x] **UI Label Fix**: Corrected "Target Length" static text.

### Intelligence Overhaul (2026-02-13)
- [x] **Smart Semantic Snapping**: No more mid-sentence cuts.
- [x] **Context Expansion**: Short clips are auto-extended.
- [x] **Series Splitting**: Long clips become Part 1/2.
- [x] **Smart Download**: Fixed partial download speed (10x faster).

---

## 🔮 FUTURE ROADMAP

### Phase 6: Advanced Intelligence
- [ ] **Multi-Speaker Diarization**: Improved handling for podcasts with frequent switching
- [ ] **Visual Scoring Enhancement**: Better b-roll potential rating

### Phase 7: Social & Viral
- [ ] **Auto-Hashtags**: LLM-generated viral metadata
- [ ] **Batch Processing**: Process multiple videos in queue

### Feature Requests
- [ ] **B-Roll Integration**: Logic to insert B-Roll during "dry" scenes (User Priority).


### 🔧 Tech Debt / Long Term
- [ ] **Replace CTranslate2**: Monitor `faster-whisper` or `ctranslate2` repos for a fix to the CUDA destructor segfault (Exit 0xC0000005).
    - Current workaround: Subprocess isolation + Exit code suppression.
    - If fixed upstream, revert to in-process transcription for speed.

---

## 🛑 BUGS / KNOWN ISSUES
- **UI Padding**: Sidebar has unwanted top/bottom gaps (User Priority #1)
- [ ] **Bare except blocks**: Lint warnings in main_ui.py and analyzer.py
- [x] **Caption Size Bug**: User reports 80px settings ignored (Fixed: Added event handler).

- **MediaPipe Warnings**: `inference_feedback_manager` spam in console (cosmetic)
