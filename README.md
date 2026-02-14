# AI Video Engine 🎬

A powerful, local-first AI video generation app built with **Electron**, **React**, and **FastAPI**.
Takes a YouTube URL and uses local LLMs (Ollama) and Whisper to automatically detect, crop, and caption viral short clips.

## 🏗️ Architecture
- **Frontend**: React + Vite + TailwindCSS + Shadcn/UI
- **Backend**: Python FastAPI (Hidden process)
- **Engine**: Electron (App Shell)
- **AI**: Ollama (LLaVA/Qwen), Faster-Whisper, MediaPipe

## 🚀 How to Run (Development)

You need **3 separate terminals** to run the app in dev mode (for hot-reloading).

### Terminal 1: Backend (Python)
```bash
# Activate Virtual Environment
source .venv/Scripts/activate  # Windows
source .venv/bin/activate      # Mac/Linux

# Start FastAPI Server
python backend/api.py
```
> Server runs on `http://127.0.0.1:8000`

### Terminal 2: Frontend (React)
```bash
cd frontend
npm run dev
```
> UI runs on `http://localhost:5173`

### Terminal 3: App Shell (Electron)
```bash
cd electron
npm start
```
> Launches the desktop window connecting to localhost:5173

---

## 🤖 AI Agent Developer Guide

If you are an AI working on this project, follow these rules:

1.  **Do NOT try to run the full Electron app**. You cannot see the window.
2.  **Mock the UI**: If you need to test backend logic, use `curl` or writing a small python script in `tests/`.
3.  **Run Backend Only**:
    ```powershell
    # Windows
    .venv\Scripts\python backend/api.py
    ```
4.  **Run Frontend Build Check**:
    ```powershell
    cd frontend; npm run build
    ```
5.  **Files to Watch**:
6.  **CONTEXT LOADING (MANDATORY)**:
    At the start of *every* session, you **MUST** read these 4 files to understand the project state:
    - `PROJECT_MEMORY.md` (Architecture & Rules) -> **Source of Truth**
    - `PLAN.md` (Active Tasks)
    - `DEV_LOG.md` (History & Decisions)
    - `USER_PROMPTS.md` (User Requirements)
    
    *Do not ask the user for context.* Read these files first.

7.  **Architecture Enforcement**:
    - **Strictly follow** the Electron + React + FastAPI pattern defined in `PROJECT_MEMORY.md`.
    - Do **NOT** re-introduce Flet or other UI frameworks.
    - Always use the `.venv` for Python operations.

## 📦 How to Build (Production)

To create a standalone `.exe` installer:

1. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Package Electron App**:
   ```bash
   cd electron
   npm run dist
   ```

3. **Locate Installer**:
   The final executable will be in:  
   `e:\AI_Video_Engine\electron\dist\win-unpacked\AI Video Engine.exe`

---

## 🛠️ Configuration

- **.env**: Place your environment variables (like `OLLAMA_BASE_URL`) in the root.
- **Project Structure**:
    - `src/`: Core AI logic (shared by backend)
    - `models/`: Weights for Whisper/Ollama
    - `legacy/`: Archived Flet UI code
