# AI Video Engine: User Prompt History & Vision Evolution

Documenting the evolution of user expectations from a "Hardware Hack" to a "World-Class Creator Suit."

## 🧭 Milestone 1: The Hardware-Aware AI (Genesis)
- **Prompt**: "Glue it piece by piece... for my specific hardware (RTX 4060)."
- **Constraint**: The Lenovo LOQ hardware (8GB VRAM) was the ultimate governor for the "Sequential Loading" pattern.
- **Outcome**: The first modular `src/` core.

## 🎨 Milestone 2: Visual Professionalism (The Captions Era)
- **Prompt**: "I want 5 stunning Alex Hormozi presets... world-class look."
- **Evolution**: Built the `.ass` karaoke engine. High-contrast colors, yellow highlights, and "Pop" animations became the standard.
- **Key Discovery**: Users value "Visual Energy" as much as accurate clipping.

## 🚀 Milestone 3: The UX Revolution (The Electron Pivot)
- **Prompt**: "The Flet UI is complete shit. Make it professional like Opus.pro."
- **Transformational Requirements**:
    - **Sticky Preview**: User wanted to see changes in real-time while tweaking font size at the bottom of the sidebar.
    - **Global Colors**: Request to change Box/Outline colors for *any* preset, including Hormozi, without turning on "Custom Mode."
    - **Integrated Terminal**: Real-time feedback in the app instead of a background console.

## 🛡️ Milestone 4: Content Integrity (The "Vibe" Era)
- **Prompt**: "The AI is cutting mid-sentence. It ruins the vibe."
- **Technical Response**: **Semantic Snapping**. Prioritized thought-completion over strict scene boundaries.
- **Expansion**: "Short clips are being ignored." -> Implemented **Context Expansion** to rescue high-viral-score hooks.

## 🧱 Milestone 5: The Stability Foundation (Ollama & VRAM)
- **Prompt**: "The core app is broken. Ollama connection refused. Memory errors."
- **Root Cause**: Aggressive timeouts (2s) and VRAM leaks when running multiple AI models sequentially.
- **Solution**:
    - **Robustness**: Retry logic + exponential backoff for AI connections.
    - **Resource Management**: Explicit `unload_model()` + GC hooks between pipeline stages.
    - **Sync**: Pre-flight checks to prevent "Zombie" frontend requests.

## 🎨 Milestone 6: The Modern Interaction Layer (UX Polish)
- **Prompt**: "The sidebar is cluttered. Live Preview overlaps the scrollbar. Make it 2026 stunning."
- **Feedback**: "Show download progress in the UI terminal... I want to see what's happening."
- **Execution**:
    - **Sidebar Refactor**: Split into `TabMedia`, `TabAI`, `TabStyle` with independent scrolling.
    - **Visual Hierarchy**: Fixed headers for "Live Preview" so it never scrolls out of view.
    - **Real-Time Feedback**: Piped `yt-dlp` and `Whisper` logs directly to the frontend WebSocket terminal.

## 🎛️ Milestone 10: Control & Customization (The Editor Era)
- **Prompt**: "Caption positioning is good... but let the user decide in an editor?"
- **Prompt**: "Let there be an option to turn on B-Roll, and multi speaker on/off."
- **Execution**:
    - **Interactive Editor**: Created a "Drag-and-Drop" visual editor (`CaptionEditorModal`) for precise caption placement.
    - **Global Toggles**: Added "Smart B-Roll" and "Video Podcast" switches in the Sidebar to give users granular control over the AI pipeline.
    - **Live Preview**: Added video player to the editor for immediate feedback.

## 📈 Priority Roadmap (User-Prioritized)
| Feature | Progress | Status |
| :--- | :--- | :--- |
| **RTX 4060 Stability** | 100% | Sequential loading + Subprocess Worker. |
| **Ollama Robustness** | 100% | Retry logic + Pre-flight Checks (Milestone 5). |
| **Memory Management** | 100% | Explicit VRAM unloading + GC hooks. |
| **UX/UI Modernization** | 100% | Sidebar Tabs + Non-overlapping Layouts. |
| **B-Roll Integration** | 100% | Pexels API + Keyword Matching (Phase 9). |
| **Interactive Editor** | 100% | Visual Caption Positioning (Phase 10). |
| **Performance (Render)** | 100% | Process Priority Optimization (Milestone 11). |
| **Global Error Handling**| 0% | Future Work (Phase 12). |

## 📝 Pending Requests & Observations
- "The app becomes very laggy while rendering... everything becomes slow." (Optimize Render Priority?)
- "Generated clips lack the virality score." (UI Integration needed).
- "Progress bar... needs to be more detailed, with ETA for each task."


-------------------------------------------------

Can you remove font family from main and move it to the custom tab?

also, can you also add a font size slider to the custom tab?