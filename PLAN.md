# Project Roadmap & Active Strategy

> **Purpose**: This file tracks **WHAT** needs to be done next.
> **Rule**: When a task is completed, move it to `PROJECT_MEMORY.md` (History) and delete it from here.

## 🚧 ACTIVE TASKS (High Priority)

### Core Engine
- [ ] **Critical Architecture Pivot**: Refactor `renderer.py` to use **ASS Subtitles** instead of MoviePy `TextClip`. (Solves speed/style limitations).
- [ ] **Advanced Scene Detection**: Integrate `PySceneDetect` before analysis to provide better cut points.
- [ ] **Scene-Aware Cropping**: Sync camera position logic with scene boundaries to prevent drifting during shot changes.
- [ ] **Active Speaker Detection**: Improve logic to correctly identify and focus on the active speaker.
- [ ] **Download Optimization**: Further tune segment fetching speed.

### AI Intelligence
- [ ] **AI Brain Enhancement**: Optimize prompt/logic to identify higher volume of high-potential clips.
- [ ] **Retention Scoring**: Implement 3-point frame sampling (Start/Mid/End) for better virality prediction.
- [ ] **VRAM Optimization**: Ensure stability for 4GB/6GB cards. (not that important now)

### UI & Logging
- [ ] **UI Responsiveness**: Fix CSS layout scaling on resize.
- [ ] **Live Log Mirroring**: Stream actual terminal logs to the UI console.
- [ ] **Log Sanitization**: Suppress internal MediaPipe warnings.

---

## 🔮 FUTURE ROADMAP

### Phase 6: Advanced Intelligence
- [ ] **Multi-Speaker Diarization**: Improved handling for podcasts with frequent switching.
- [ ] **Visual Scoring**: Enhance VisionAnalyzer to rate "b-roll" potential.

### Phase 7: Social & Viral
- [ ] **Subtitle Animation**: Add "Karaoke-style" word highlighting (dynamic ASS filters).
- [ ] **Auto-Hashtags**: LLM-generated viral metadata.

---

## 🛑 BUGS / KNOWN ISSUES
- **MediaPipe Warnings**: `inference_feedback_manager` spam in console (safe to ignore but annoying).
- **Download Parse Error**: Occasional `Stream #0:1` metadata parsing issue with `yt-dlp`.
