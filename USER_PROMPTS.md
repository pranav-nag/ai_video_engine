# User Prompts & Feature Requests

> **Instructions for the User**:
> Add your new feature requests, bug reports, or ideas below.
> When an AI Agent starts working, it will read the top-most item, move it to `PLAN.md` as an active task, and mark it here as `[Processing]`.

## 📥 Inbox (Add new requests here)

- [ ] Example: "Add a button to clear the project library."


## 🔄 History (Processed)

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


- [ ] **Caption Size Bug**: User sets 80px, but it defaults. (Debugging in progress - Logs added)
- [ ] **Feature Request**: B-Roll Integration. (Moved to PLAN.md)
- [x] **UI Bug**: Target Length Label mismatch. (Fixed)
