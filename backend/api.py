import sys
import os
import threading
import asyncio
import traceback
from typing import Optional, Dict, Any
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from backend.websocket_manager import ConnectionManager
from src.pipeline import run_ai_pipeline
from src.logger import VideoLogger


# --- Models ---
class VideoRequest(BaseModel):
    url: str
    style: str = "Hormozi"
    resolution: str = "1080p"
    min_sec: int = 15
    max_sec: int = 60
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    caption_size: int = 60
    caption_pos: str = "center"
    focus_region: str = "center"
    output_bitrate: str = "5000k"
    output_resolution: str = "1080x1920"
    content_type: str = "General"
    custom_config: Optional[Dict[str, Any]] = None


# --- App Setup ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global loop
    loop = asyncio.get_event_loop()
    print("🚀 Backend Startup Complete")
    yield
    # Shutdown
    print("🛑 Shutting down backend...")
    if processing_thread and processing_thread.is_alive():
        cancel_event.set()

    try:
        from src.cleanup import cleanup_temp_files

        cleanup_temp_files()
    except Exception as e:
        print(f"Cleanup error: {e}")


app = FastAPI(title="AI Video Engine Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()
cancel_event = threading.Event()
processing_thread = None

processing_thread = None


# --- Helpers ---
class WebSocketLogger:
    """Adapter to make VideoLogger write to WebSocket"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.video_logger = VideoLogger()
        self.video_logger.setup("Backend_Session")

        # Monkey patch the internal logger to also broadcast
        # simpler way: pass a ui_callback to setup, if VideoLogger supports it.
        # VideoLogger.setup() takes ui_callback.

        # We need to re-setup with our callback
        self.video_logger.setup("Backend_Session", ui_callback=self.ws_log_callback)

    def ws_log_callback(self, message, color=None):
        # Convert log colors to CSS/Tailwind colors
        # Simple mapping for now
        css_color = "text-white"
        if color == "red" or "❌" in message:
            css_color = "text-red-500"
        elif color == "green" or "✅" in message:
            css_color = "text-green-500"
        elif color == "blue" or "🔗" in message:
            css_color = "text-blue-400"
        elif color == "orange" or "⚠️" in message:
            css_color = "text-orange-400"
        elif color == "cyan":
            css_color = "text-cyan-400"
        elif color == "purple" or "🧠" in message:
            css_color = "text-purple-400"

        asyncio.run_coroutine_threadsafe(self.manager.log(message, css_color), loop)

    def log(self, message, color=None):
        self.video_logger.log(message, color=color)

    def info(self, message):
        self.video_logger.info(message)

    def error(self, message):
        self.video_logger.error(message)

    def rename_log_file(self, name):
        self.video_logger.rename_log_file(name)

    def capture_ollama_logs(self):
        self.video_logger.capture_ollama_logs()


# --- Routes ---


@app.get("/")
def health_check():
    return {"status": "online", "service": "AI Video Engine API"}


class MetadataRequest(BaseModel):
    url: str


@app.post("/metadata")
def get_metadata(req: MetadataRequest):
    try:
        from src.ingest_transcribe import VideoIngestor

        ingestor = VideoIngestor()
        duration, title = ingestor.get_video_info(req.url)
        return {"status": "success", "duration": duration, "title": title}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/process")
def start_process(req: VideoRequest, background_tasks: BackgroundTasks):
    global processing_thread

    if processing_thread and processing_thread.is_alive():
        return {"status": "error", "message": "Already processing"}

    cancel_event.clear()

    # Define wrapper to run synchronously in thread but allow async logging
    def worker():
        # Adapter for Progress
        def progress_callback(p, msg):
            if msg.startswith("CLIP_READY:"):
                clip_data = msg.replace("CLIP_READY:", "").split("|")
                if len(clip_data) >= 2:
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(
                            {
                                "type": "clip_ready",
                                "path": clip_data[0],
                                "title": clip_data[1],
                            }
                        ),
                        loop,
                    )
            else:
                asyncio.run_coroutine_threadsafe(manager.progress(p, msg), loop)

        # Adapter for Logger
        ws_logger = WebSocketLogger(manager)

        try:
            run_ai_pipeline(
                url=req.url,
                style=req.style,
                res=req.resolution.replace("p", ""),  # Input might be '1080p'
                min_sec=req.min_sec,
                max_sec=req.max_sec,
                start_time=req.start_time,
                end_time=req.end_time,
                caption_size=req.caption_size,
                caption_pos=req.caption_pos,
                focus_region=req.focus_region,
                output_bitrate=req.output_bitrate,
                output_resolution=req.output_resolution,
                content_type=req.content_type,
                custom_config=req.custom_config,
                logger=ws_logger,
                progress_callback=progress_callback,
                cancel_event=cancel_event,
            )
        except Exception as e:
            traceback.print_exc()
            asyncio.run_coroutine_threadsafe(
                manager.log(f"🔥 Critical Error: {str(e)}", "text-red-500"), loop
            )

    processing_thread = threading.Thread(target=worker, daemon=True)
    processing_thread.start()

    return {"status": "started", "config": req.model_dump()}


@app.post("/cancel")
def cancel_process():
    if processing_thread and processing_thread.is_alive():
        cancel_event.set()
        return {"status": "cancelling"}
    return {"status": "ignored", "message": "Nothing running"}


def check_ollama():
    try:
        import requests

        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=1)
        if resp.status_code == 200:
            print("✅ Ollama is RUNNING")
        else:
            print(f"⚠️ Ollama returned status {resp.status_code}")
    except:
        print("❌ Ollama is NOT running. Please start it for AI features.")


if __name__ == "__main__":
    check_ollama()
    print(f"Backend starting via: {sys.executable}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
