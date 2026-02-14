# AI Video Engine 🎬

A premium, local-first AI video generation suite. It transforms long-form YouTube content into viral, highly-edited short clips using local LLMs and hardware-accelerated rendering.

---

## ✨ Features
- **Hybrid Architecture**: Native performance with **Electron**, modern UI with **React (Shadcn/UI)**, and high-performance AI processing with **FastAPI**.
- **Local AI Intelligence**:
  - **Ollama Integration**: Automated viral analysis using `qwen2.5:7b` (with auto-fallback to available models).
  - **Vision Analysis**: Scene-aware analysis with `minicpm-v`.
  - **Whisper Transcription**: Subprocess-isolated transcription (no VRAM crashes).
- **Pro Video Engine**:
  - **Smart Cropping**: MediaPipe-powered face tracking and scene-snap logic.
  - **Advanced Captions**: Karaoke-style `.ass` subtitles with "Pop" animations and multi-style presets (Hormozi, Neon, Beast, etc.).
  - **Hardware Acceleration**: NvEnc-optimized h264/h265 encoding for NVIDIA GPUs.
- **Integrated Terminal**: Real-time log streaming directly in the UI.

---

## 🏗️ Tech Stack
- **Frontend**: React 18, Vite, TailwindCSS, Framer Motion, Radix UI.
- **Backend**: Python 3.12 (FastAPI), WebSockets, Asyncio.
- **AI Models**: Faster-Whisper (v3 Turbo), Ollama (Qwen/Llama), MediaPipe.
- **Shell**: Electron (Window & Process Management).

---

## 💻 Hardware Requirements
**Minimum Specifications:**
- **OS**: Windows 10/11 (64-bit)
- **GPU**: NVIDIA RTX 3060/4060 (8GB VRAM Required for concurrent Vision/Text analysis)
- **RAM**: 16GB+
- **Storage**: 20GB Free Space (Models + Cache)

---

## 🚀 Getting Started

### The Fast Way (One-Click)
Just run the unified batch script in the root directory:
```powershell
./run.bat
```
*This will handle frontend building and launch the Electron app automatically.*

### Manual Dev Mode
If you need hot-reloading for development:
1. **Backend**: `.venv\Scripts\python backend/api.py` (Port 8000)
2. **Frontend**: `cd frontend && npm run dev` (Port 5173)
3. **Electron**: `cd electron && npm start`

---

## 🤖 AI Agent Guidelines
If you are an AI working on this codebase, you **must** follow the documentation protocol:

### 1. Unified Project Brain
All project context and logic are stored in the `brain/` folder. Read these first:
- `brain/project_memory.md`: **Single Source of Truth** for architecture and operational rules.
- `brain/plan.md`: Current roadmap and active tasks.
- `brain/dev_log.md`: Chronological log of decisions and session outcomes.
- `brain/user_prompts.md`: History of user requests and feature statuses.

### 2. Operational Rules
- **Environment**: Always use the local `.venv`.
- **Infrastructure**: Electron + React + FastAPI. **No other frameworks.**
- **GPU Safety**: Transcription is isolated in a subprocess to prevent memory leaks/segfaults.

---

## 📦 Building for Production
1. Build the React UI: `cd frontend && npm run build`
2. Package with Electron Builder: `cd electron && npm run dist`
3. Output found in: `electron/dist/`

---

## 🛠️ Configuration
- **.env**: Local config (e.g., `OLLAMA_BASE_URL`).
- **assets/**: Background music and B-roll clips for creative editing.
- **legacy/**: Archived code from the initial Flet transition.
