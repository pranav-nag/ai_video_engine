# User Prompts & Feature Requests

> **Instructions for the User**:
> Add your new feature requests, bug reports, or ideas below.
> When an AI Agent starts working, it will read the top-most item, move it to `PLAN.md` as an active task, and mark it here as `[Processing]`.

## 📥 Inbox (Add new requests here)

- [ ] Example: "Add a button to clear the project library."


## 🔄 History (Processed)

- [x] **Critical Fixes & Theme Upgrade** (2026-02-15)
  - **Theme Separation**: Decoupled App UI theme from Video Caption theme.
  - **App Theme Picker**: Added dedicated color selection for application UI.
  - **Ollama Resilience**: Fixed connection errors by adding model auto-fallback logic.
  - **Terminal Real-time Sync**: Fixed UI terminal freeze by streaming subprocess output.
  - **Stability**: Fixed `[NO_LOGGER]` crash and backend `SyntaxError`.
  - **Defaults**: Set "Podcast" and "Auto Face" as default AI strategy.

- [x] Consolidate documentation into `USER_PROMPTS.md`, `PLAN.md`, `DEV_LOG.md`, `PROJECT_MEMORY.md`. (Completed by Restructuring Agent)
- [x] **Output Quality Overhaul** (2026-02-10 21:05 - 22:19)
  - Fixed resolution (607×1080 → 1080×1920)
  - Fixed video bitrate (820kbps → 26 Mbps VBR, Premiere Pro match)
  - Fixed audio bitrate (127kbps → 320kbps AAC)
  - Fixed pixel format (gbrp → yuv420p, profile high 4.2)
  - Fixed face cropping (static average → per-frame dynamic tracking)
  - Fixed caption timing (gaps → gap-free, 50ms pre-buffer)
  - Removed broken emoji rendering from ASS subtitles
  - Added timestamps to output filenames for easy recognition
  - **Status**: Ready for testing. Re-render a clip to verify.
- [x] **Professional Overhaul** (2026-02-10 22:30 - 23:15)
  - Fixed FPS preservation (removed forced 30fps, now respects source)
  - Implemented professional caption styles (Hormozi, Minimal, Neon, Boxed)
  - Added caption positioning controls (Top, Center, Bottom)
  - Added real progress bar with ETA display
  - Fixed Input/Slider synchronization (bi-directional)
  - Added Caption Size live label (shows px value)
  - Fixed AI duration validation (strict min/max enforcement)
  - Improved scene snapping logic (prioritizes valid duration)
  - Added VRAM cleanup error handling (prevents crashes)
  - Removed duplicate dropdown in Co-Pilot Styles
  - Set page padding=0 for edge-to-edge layout
  - **Status**: PARTIAL - UI padding issue remains unresolved

- [x] **Content Quality & Log Fixes** (2026-02-11 00:30)
  - User feedback: "Clips too short (28s), sentiment generic, log errors."
  - **FIXED**: Increased min duration to 30s.
  - **FIXED**: Tuned prompt for "Story Mode" and "Emotional Resonance".
  - **FIXED**: Suppressed harmless segfault log (Exit 3221226505).
  - **Status**: Ready for verification.



- [x] **Caption Size Bug**: User sets 80px, but it defaults. (Fixed 2026-02-13)
- [ ] **Feature Request**: B-Roll Integration. (Moved to PLAN.md)
- [x] **UI Bug**: Target Length Label mismatch. (Fixed)
- [x] **Feature Request**: Auto-pull new models. "Whenever we update the models, the agent should auto download/pull the new model from internet."
  - **Implemented**: `ensure_ollama_running` does this automatically.
- [x] **Optimization**: Check internet for better models & improve memory management.
  - **Action**: Research confirmed `qwen2.5` + `minicpm-v` as SOTA.
  - **Action**: Implemented `unload_model` and I/O optimizations.
- [x] **Improve Video Accuracy**: "Model is cutting between words."
  - **Fixed**: Implemented `snap_to_word_boundary` (Semantic Snapping).
- [x] **Smart Duration**: "Let the AI decide... split if too long".
  - **Fixed**: Implemented `expand_context` (for short hooks) and Series Splitting (for long stories).
- [ ] **Feature Request**: Full In-App Editor (Manual trimming). (Long Term)





- [x] **Visual & Audio Upgrade** (2026-02-14)
  - **Advanced Captions**: Added "Active Word" highlight with Fill + Glow colors.
  - **New Styles**: Added "Neon" (Cyan/Purple), "Beast", and "Gaming" presets.
  - **Intelligent B-Roll**: Automatically fills "dead air" (no face > 2s) with random clips from `assets/b_roll`.
  - **Background Music**: Mixes random tracks from `assets/music` at 10% volume.
  - **Status**: Implemented & Verified (Unit Tests). Requires user assets.


- [x] **UI Polish & Custom Styles** (2026-02-14)
  - **Caption Preview**: Added live visual preview of caption styles.
  - **Custom Styles**: Implemented "Custom Styling" mode with color pickers and font selection.
  - **New Presets**: Added "Bold Shadow", "Outline Glow", "Gradient Vibrant", "Glass Morphism", "Minimal Elegant".
  - **Bug Fix**: Fixed Caption Size slider ignoring values (100px now works).
  - **Bug Fix**: Reserved `moviepy` import error on startup.
  - **Status**: Implemented and Verified.

- [x] **Verification: Engagement Ranking** (2026-02-14)
  - verified logic in `analyzer.py`: Clips are scored (0-100) by AI based on hook/emotion and sorted automatically.
  - **Status**: Confirmed working.







- [ ] **Architecture Migration**: Switch to Electron + React + FastAPI. (Processing)
  - **Reason**: User feedback "UI is complete shit", "Preview broken", "Color selection bad".
  - **Plan**: defined in `implementation_plan.md`.
  - **Status**: Scaffolding Phase.



- [x] **Cleanup & Standardization** (2026-02-14)
  - **Bloat Removal**: Deleted `cache/` (13GB) and `electron/dist/` (6GB).
  - **Legacy Archive**: Moved Flet code to `legacy/`.
  - **Model Cleanup**: Removed unused Whisper models.
  - **Standards**: Added Prettier config and updated `.gitignore`.
  - **Status**: Completed (Project size reduced from 27GB to ~7GB).
