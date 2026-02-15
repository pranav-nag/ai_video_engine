# Task: Phase 6: Super-Captions (Opus-Style Visuals)

## 🎨 Visual Intelligence (Keywords & Emojis)
- [x] Analyze `renderer.py` to determine caption rendering method (MoviePy vs. FFmpeg/ASS) <!-- id: 0 -->
- [x] Create `src/caption_enhancer.py`: Module to detect "Power Words" and suggest emojis (Dictionary-based) <!-- id: 1 -->
- [x] Update `pipeline.py` to run `caption_enhancer` after transcription <!-- id: 2 -->
- [x] Modify `renderer.py` (via `fast_caption.py`) to support **Multi-Color Captions** and **Emojis** <!-- id: 3 -->
- [x] Modify `renderer.py` to render Emojis in captions (via Font Override) <!-- id: 4 -->

## 🟡 Phase 7: Multi-Cam Intelligence (Podcasts)
- [x] Create `src/layout_engine.py`: Logic to detect 1 vs 2 speakers (Faces) <!-- id: 7 -->
- [x] Implement `detect_dual_faces` in `layout_engine.py` (OpenCV) <!-- id: 8 -->
- [x] Modify `renderer.py` to support `render_split_screen` (Top/Bottom Stack) <!-- id: 9 -->
- [x] Update `pipeline.py` to auto-select Layout Mode based on face count <!-- id: 10 -->


## 🟣 Phase 8: Polish & Transitions
- [x] Implement smooth Audio Crossfades <!-- id: 11 -->
- [x] Add Digital Zoom cuts <!-- id: 12 -->


## 🔵 Phase 10: Interactive Editor & Global Toggles
- [x] Add Global Toggles for B-Roll & Split-Screen in Backend (`api.py`) <!-- id: 16 -->
- [x] Update `pipeline.py` and `renderer.py` to respect Toggles <!-- id: 17 -->
- [x] Add Switches in Frontend `App.tsx` <!-- id: 18 -->
- [x] Create Frontend `CaptionEditorModal.tsx` (Drag-and-Drop) <!-- id: 19 -->
- [x] Implement `rerender_clip` endpoint in Backend <!-- id: 20 -->

### Verification
- [x] Verify Frontend Build (`npm run build`) <!-- id: 21 -->
- [x] Verify Backend Syntax (`py_compile`) <!-- id: 22 -->


## 🟢 Phase 9: B-Roll & Stock Footage
- [x] Create `src/b_roll_manager.py` (or update existing) to index `assets/b-roll` <!-- id: 13 -->
- [x] Implement Keyword Matching (e.g., "Money" -> `money.mp4`) <!-- id: 14 -->
- [x] Modify `renderer.py` to overlay B-Roll on top of the main clip <!-- id: 15 -->
## 🟠 Phase 11: Performance & UX Polish
- [x] Implement Render Priority Management (`psutil`) <!-- id: 23 -->
- [x] Integrate SQLite `JobManager` for persistence <!-- id: 24 -->
- [x] Add ETA calculations to Progress Tracker <!-- id: 25 -->
- [x] Create Automated Font Downloader & Verifier <!-- id: 26 -->
- [x] UI Readability Overhaul (Increase label sizes) <!-- id: 27 -->
- [x] Duplicate Font Size slider to Main tab <!-- id: 28 -->

## 🔵 Phase 12: Roadmap
- [ ] Implement global exception handling in FastAPI <!-- id: 29 -->
- [ ] Add Smart B-Roll and Multi-Speaker toggles to UI <!-- id: 30 -->
- [ ] Live Preview in caption editor <!-- id: 31 -->
- [ ] Integration: Virality Score Display on Clip Cards <!-- id: 32 -->
