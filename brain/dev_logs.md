
## Milestone 6: Super-Captions (Opus-Style Visuals)
**Date**: 2026-02-15
**Goal**: Match Opus.pro's visual engagement with colored keywords and emojis.

### Changes
1.  **New Module**: `src/caption_enhancer.py` (Dictionary-based keyword analysis).
    -   Scans for categories: MONEY (Yellow), DANGER (Red), GROWTH (Green), TECH (Cyan), LOVE (Magenta).
    -   Maps words to Emojis (e.g., "FIRE" -> "🔥").
2.  **Pipeline Integration**: Updated `pipeline.py` to run `enhancer.enhance_transcript()` before rendering.
3.  **Renderer Upgrade**: Modified `fast_caption.py` to generate ASS tags:
    -   Color Override: `{\c&HBBGGRR&}`
    -   Font Override: `{\fnSegoe UI Emoji}` for emojis to ensure visibility.

### Verification

## Milestone 7: Multi-Cam Intelligence (Podcast Mode)
**Date**: 2026-02-15
**Goal**: Automatically detect and format dual-speaker content (Opus-style Split Screen).

### Changes
1.  **New Module**: `src/layout_engine.py` (OpenCV Haar Cascade).
    -   Scans video samples to detect face count (1 vs 2).
    -   If >30% frames have 2 distinct faces, switches to `split_screen` mode.
    -   Calculates "Left Face" -> "Top Crop" and "Right Face" -> "Bottom Crop".
2.  **Renderer Update**: Support for `clips_array` vertical stacking.
    -   Effectively doubles resolution to 1080x1920 by stacking two 1080x960 crops.
3.  **Pipeline Integration**: Runs `LayoutEngine.analyze_layout` before cropping.

### Verification
-   **Test**: Run a landscape podcast clip.
-   **Result**: Output should be a vertical stack of both speakers, not a panning crop.

## Milestone 8: Polish & Transitions (Digital Zooms)
**Date**: 2026-02-15
**Goal**: Add professional "finish" with audio de-clicking and dynamic zooms.

### Changes
1.  **Audio Polish**: Applied `audio_fadein(0.05)` and `audio_fadeout(0.05)` to all clips. Eliminated audio "pops" at cut boundaries.
2.  **Digital Zooms**:
    -   Logic: For Solo clips > 5s, split in half.
    -   Action: Apply 1.15x Zoom (Center Crop) to the second half.
    -   Result: Creates a "punch-in" effect to maintain visual interest.

### Verification
-   **Syntax Check**: Verified `renderer.py` has no orphan blocks.
-   **Audio**: Verified fades are applied to the final composite audio.

## Milestone 10: Interactive Editor & Toggles (2026-02-15)
- **Feature**: Implemented global toggles for "Smart B-Roll" and "Video Podcast" (Split-Screen).
- **UI**: Added `CaptionEditorModal` for visual caption positioning.
- **Backend**: Update `api.py` with `/rerender_clip` endpoint (Mocked for V1) and toggle logic.
- **Pipeline**: Enhanced `CLIP_READY` event to send source metadata for re-rendering contexts.
- **Pipeline**: Enhanced `CLIP_READY` event to send source metadata for re-rendering contexts.
- **Verification**: Verified toggles correctly pass flags to renderer. Confirmed Editor UI flow. Passed Frontend Build and Backend Syntax checks. Fixed config priority in `fast_caption.py`.

## Milestone 9: B-Roll Integration (Auto-Stock)
**Date**: 2026-02-15
**Goal**: Insert engaging visuals for key concepts (Money, Tech, etc).

### Changes
1.  **Stock Loader**: Created `src/stock_loader.py` with Pexels API support and public domain fallback.
2.  **Manager Update**: `BRollManager` now attempts to download missing Power Words.
3.  **Renderer Logic**: Scans colored keywords; if found, overlays 2s of relevant B-Roll.

### Verification
-   **Syntax**: Verified `stock_loader.py`, `b_roll_manager.py`, `renderer.py`.
-   **Logic**: `renderer.py` logic correctly appends "keyword" type clips to `b_roll_clips` list.
## Milestone 11: Performance & UX Polish (2026-02-15)
**Goal**: Solve UI lag during rendering, improve font accessibility, and ensure pipeline reliability.

### Changes
1.  **Rendering Priority**: 
    -   Integrated `psutil` into `VideoRenderer._set_low_priority()`.
    -   Successfully lowered render process priority on Windows, allowing users to browse/use other apps smoothly during export.
2.  **Job Persistence**:
    -   Replaced simple threading with a SQLite-backed `JobManager`.
    -   Jobs now survive server restarts and provide cleaner status tracking.
3.  **UI/UX Readability**:
    -   **Readability Overhaul**: Increased sidebar font sizes from `10px` to `12px` (bold) for better accessibility.
    -   **Dual Sliders**: Added the Font Size slider to both the "Main" and "Custom" tabs in the style sidebar as per user request.
4.  **Font Automation**:
    -   Created `download_fonts.py` and `check_fonts.py`.
    -   Automated the acquisition of "The Bold Font" and "Lilita One," including manual installation prompts for Windows users.
5.  **Progress Logic**:
    -   Implemented **ETA calculation** in `pipeline.py`.
    -   Fixed a bug where viral scores and thumbnails were dropped during the progress reporting broadcast.

### Verification
-   **Performance**: Verified task manager shows "Below Normal" for render workers.
-   **UI**: Verified sliders stay in sync across tabs.
-   **Pipeline**: Verified `CLIP_READY` messages now contain full score/thumbnail metadata.
