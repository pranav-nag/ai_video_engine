# Project Roadmap & Active Strategy

> **Purpose**: This file tracks **WHAT** needs to be done next.
> **Rule**: When a task is completed, move it to `PROJECT_MEMORY.md` (History) and delete it from here.

## 🚧 ACTIVE TASKS (High Priority)

### UI Polish (URGENT)
- [ ] **Sidebar Layout**: Fix top/bottom padding/margin gaps in sidebar
    - User wants true edge-to-edge layout (zero gaps at window borders)
    - Current status: spacing=0 applied but visual gaps remain
- [ ] **Responsive Layout**: Ensure all controls visible at different window sizes

### Testing & Quality
- [ ] **Long-form Stress Test**: Run 20+ minute video to verify subprocess stability
- [ ] **Competitor Analysis**: Side-by-side comparison with Opus.pro, Klap.app outputs

---

## ✅ RECENTLY COMPLETED (2026-02-11)

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
- [x] **Content Type UI**: Added Auto/Podcast/Solo dropdown.
- [x] **UI Label Fix**: Corrected "Target Length" static text.



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
- **Caption Size Bug**: User reports 80px settings ignored (Debugging in progress).

- **MediaPipe Warnings**: `inference_feedback_manager` spam in console (cosmetic)
