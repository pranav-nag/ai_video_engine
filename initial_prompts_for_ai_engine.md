### 🛠️ The Final "Pro-Level" Prompts

Here are the corrected prompts. I have added the **Disk Space Protection** and **UI Threading** logic.

### Prompt 1: The "Zero-C-Drive-Impact" Setup

*Changes: Added pip cache redirection and FFMPEG manual download handling to avoid C: drive usage.*

code Text

```markdown
I am building a local AI video repurposing software on my Windows laptop (Ryzen 7 7435HS, RTX 4060 8GB VRAM, 24GB RAM). 
Target Storage: External SSD (E: Drive). C: Drive is FULL, so absolutely NO temp files on C:.

Please create a script `setup_project.py` that:
1. Defines base path `E:/AI_Video_Engine`.
2. Creates this folder structure:
   - `assets/fonts`, `assets/overlays`
   - `cache/huggingface`, `cache/ollama`, `cache/pip_temp` (Crucial)
   - `temp`, `output`, `src`
3. Generates a `.env` file containing:
   - HF_HOME=E:/AI_Video_Engine/cache/huggingface
   - OLLAMA_MODELS=E:/AI_Video_Engine/cache/ollama
   - TORCH_HOME=E:/AI_Video_Engine/cache/torch
   - XDG_CACHE_HOME=E:/AI_Video_Engine/cache
4. Generates a `requirements.txt` with:
   - faster-whisper, yt-dlp, moviepy, opencv-python, mediapipe, flet, python-dotenv, colorama, requests, psutil.
5. Prints a specific BAT file content (to be saved manually as `install.bat`) that runs the install command using the E: drive for caching to save C: space:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --cache-dir "E:\AI_Video_Engine\cache\pip_temp"`
   - `pip install -r requirements.txt --cache-dir "E:\AI_Video_Engine\cache\pip_temp"`
```

---

### Prompt 2: Ingest with Strict VRAM Cleaning

*Changes: Verified imports and added explicit garbage collection log messages.*

code Text

```markdown
Create `src/ingest_transcribe.py`.

Requirements:
1. Load environment variables from `.env` immediately to ensure models download to E:.
2. Class `VideoIngestor`: 
   - Uses `yt-dlp`. 
   - MUST configure yt-dlp to use `E:/AI_Video_Engine/temp` for all temporary download chunks (do not use default temp).
   - Return path of downloaded file.
3. Class `Transcriber`: 
   - Initialize `faster_whisper.WhisperModel` with `model_size_or_path="distil-large-v3"`.
   - Device: "cuda", Compute Type: "float16".
   - Method `transcribe(path)`: Returns list of dicts `[{"start": float, "end": float, "word": str}]`.
4. VRAM Safety: 
   - Implement a static method `free_memory()` that runs: `del model`, `gc.collect()`, `torch.cuda.empty_cache()`.
   - Call this automatically at the end of transcription.
```

---

### Prompt 3: Analyzer (Ollama Local Launcher)

*Changes: Added logic to ensure we are hitting the customized Ollama instance, not the system service.*

code Text

```markdown
Create `src/analyzer.py`.

Requirements:
1. Helper Function `ensure_ollama_running()`:
   - Check if Ollama is running. 
   - If running but not using the E: drive path, warn the user. 
   - ideally, allow the user to provide the base URL in `.env`.
2. Function `analyze_transcript(transcript_text)`:
   - Max context window management (chunk text if > 6000 words).
3. System Prompt: "You are a Viral Video Editor. Return ONLY raw JSON. No markdown formatting."
4. JSON Structure: `{"clips": [{"start": 0.0, "end": 0.0, "score": 9, "hook": "text", "reason": "text"}]}`
5. Use `requests.post` to `http://localhost:11434/api/generate` with `stream=False` and `format="json"`.
```

---

### Prompt 4: Smart Cropper (Unchanged - Logic is good)

*Changes: Minor tweak to ensure file paths use the E: temp folder.*

code Text

```markdown
Create `src/cropper.py` using MediaPipe.

Requirements:
1. Class `SmartCropper`:
   - Input: Video path.
   - Logic: Detect face center (X-coordinate).
   - Smoothing: Use Exponential Moving Average (alpha=0.1).
   - Hysteresis: If face moves < 10% of width, keep previous crop X.
2. Output: A simple dictionary `frame_mapping` where Key=FrameNumber, Value=Crop_X_Coordinate.
3. Performance: Do NOT process every single frame if using a high FPS video. Process every 2nd frame and interpolate if needed to save time, or stick to 1:1 if 4060 handles it well (it should).
```

---

### Prompt 5: Renderer with NVENC Safeguards

*Changes: Added fallback logic. If NVENC fails, it won't crash, just run slower.*

code Text

```markdown
Create `src/renderer.py` using MoviePy.

Requirements:
1. Style: "Hormozi" (Yellow/White text, Montserrat-Bold/Impact, Stroke width 2).
2. Function `render_clip(video_path, clip_data, crop_map, output_path)`:
   - Use `CompositeVideoClip`.
   - Iterate words: If current time is within word start/end, make it Yellow and 1.1x size.
3. Encoding (The Critical Part):
   - Try to use `codec="h264_nvenc"` with `ffmpeg_params=["-preset", "p4", "-cq", "20"]`.
   - Wrap the `write_videofile` in a try/except block.
   - If NVENC fails (due to missing FFMPEG libs), print "NVENC failed, switching to CPU..." and fallback to `codec="libx264"` (standard CPU).
   - Ensure `temp_audiofile` is written to `E:/AI_Video_Engine/temp` to save C: space.
```

---

### Prompt 6: Flet UI with Threading (The "App Feel" Fix)

*Changes: Added threading so the UI doesn't freeze.*

code Text

```markdown
Create `src/main_ui.py` using Flet.

Requirements:
1. Design: Dark Mode, Left Sidebar (Ingest, Library, Settings).
2. Threading Logic:
   - The "Process Video" button MUST NOT run the heavy AI tasks on the main thread.
   - Use `threading.Thread(target=run_pipeline, args=(...))` logic.
   - Use a `queue.Queue` or a shared `Flet` Text control to update logs.
3. UI Components:
   - `ft.TextField` for YouTube URL.
   - `ft.ListView` with `expand=True` for real-time logs (e.g., "Downloading...", "Transcribing...").
   - `ft.GridView` for Clip Cards.
4. Settings Page:
   - Input fields for `HF_HOME` and `OLLAMA_MODELS` (read from .env).
5. Ensure `page.update()` is called safely from the background thread to prevent UI glitches.
```

---

### 🚀 Recommended Execution Order

1. **Run Prompt 1 First.**
    - **Action:** Copy the outputted setup_project.py code, run it.
    - **Action:** **Manually** create the install.bat file it suggests and run it. Watch the terminal to ensure it is caching to E:.
2. **Ollama Setup:**
    - Before running Python code, open your terminal (PowerShell) and type: code Powershell
        
        `$env:OLLAMA_MODELS="E:\AI_Video_Engine\cache\ollama"
        ollama serve`
        
    - Keep this terminal window open. This forces Ollama to use your E: drive.
3. **Run Prompts 2-6.**

This roadmap is now mathematically safe for your storage and optimized for your hardware. Ready to generate the code?