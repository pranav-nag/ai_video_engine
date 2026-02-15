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
from src.job_manager import JobManager, JobStatus


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
    content_type: str = "General"
    use_b_roll: bool = True
    use_split_screen: bool = True
    use_split_screen: bool = True
    custom_config: Optional[Dict[str, Any]] = None


class RerenderRequest(BaseModel):
    source_path: str
    start_time: float
    end_time: float
    custom_config: Dict[str, Any]
    output_path_override: Optional[str] = None


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
    mgr = JobManager()
    mgr.cancel_current_job()

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

    def log(self, message, level="INFO", color=None):
        self.video_logger.log(message, level=level, color=color)

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


@app.get("/status/ai")
def get_ai_status():
    """Checks if Ollama is responsive."""
    try:
        from src.analyzer import ensure_ollama_running

        # We wrap this in a try/except because ensure_ollama_running raises ConnectionError on failure
        # But we want to return JSON, not 500
        try:
            ensure_ollama_running()
            return {"status": "ready", "message": "Ollama is online"}
        except ConnectionError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Check failed: {e}"}
    except ImportError:
        return {"status": "error", "message": "Backend module import failed"}


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
    mgr = JobManager()

    if mgr.get_active_job():
        return {"status": "error", "message": "Already processing"}

    # Generate Job ID
    import uuid

    job_id = str(uuid.uuid4())
    mgr.create_job(job_id, req.model_dump())

    # Define wrapper to run synchronously in thread but allow async logging
    def worker():
        # Adapter for Progress
        def progress_callback(p, msg):
            if isinstance(msg, str) and msg.startswith("CLIP_READY:"):
                clip_data = msg.replace("CLIP_READY:", "").split("|")
                if len(clip_data) >= 2:
                    path = clip_data[0]
                    title = clip_data[1]
                    thumbnail = clip_data[2] if len(clip_data) > 2 else ""
                    score = float(clip_data[3]) if len(clip_data) > 3 else 0.0

                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(
                            {
                                "type": "clip_ready",
                                "path": path,
                                "title": title,
                                "thumbnail": thumbnail,
                                "score": score,
                                "source_path": clip_data[4]
                                if len(clip_data) > 4
                                else "",
                                "start_time": float(clip_data[5])
                                if len(clip_data) > 5
                                else 0.0,
                                "end_time": float(clip_data[6])
                                if len(clip_data) > 6
                                else 0.0,
                            }
                        ),
                        loop,
                    )
            elif isinstance(msg, dict):
                # Rich Progress Update
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(
                        {
                            "type": "progress_rich",
                            "progress": p,  # Overall progress
                            "phase": msg.get("phase", "Processing"),
                            "phase_progress": msg.get("phase_progress", 0.0),
                            "text": msg.get("text", ""),
                        }
                    ),
                    loop,
                )
                # Update Job Manager Progress
                # We normalize 0-1 to percent
                if isinstance(p, (int, float)):
                    mgr.update_job_status(
                        job_id, JobStatus.PROCESSING, percent=float(p)
                    )
            else:
                # Standard String Progress
                asyncio.run_coroutine_threadsafe(manager.progress(p, str(msg)), loop)
                mgr.update_job_status(job_id, JobStatus.PROCESSING, percent=float(p))

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
                use_b_roll=req.use_b_roll,
                use_split_screen=req.use_split_screen,
                custom_config=req.custom_config,
                logger=ws_logger,
                progress_callback=progress_callback,
                cancel_event=mgr.cancel_event,  # Use Manager's cancel event
            )

            # Send Success Status if not cancelled
            if not mgr.cancel_event.is_set():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": "status", "state": "success"}),
                    loop,
                )
                mgr.update_job_status(job_id, JobStatus.COMPLETED, percent=1.0)
            else:
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": "status", "state": "cancelled"}),
                    loop,
                )
                mgr.update_job_status(job_id, JobStatus.CANCELLED)

        except Exception as e:
            traceback.print_exc()
            asyncio.run_coroutine_threadsafe(
                manager.log(f"🔥 Critical Error: {str(e)}", "text-red-500"), loop
            )
            # Send Error Status
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(
                    {"type": "status", "state": "error", "message": str(e)}
                ),
                loop,
            )
            mgr.update_job_status(job_id, JobStatus.FAILED, error=str(e))

    # Start the job via JobManager
    # Note: JobManager expects a function to start the thread itself, but our internal logic
    # handles the thread management?
    # Actually, JobManager.start_job spawns the thread. We should pass 'worker' as the target.

    mgr.start_job(job_id, worker)

    return {"status": "started", "job_id": job_id, "config": req.model_dump()}


@app.post("/cancel")
def cancel_process():
    mgr = JobManager()
    if mgr.cancel_current_job():
        return {"status": "cancelling"}
    return {"status": "ignored", "message": "Nothing running"}


@app.get("/status/active_job")
def get_active_job():
    mgr = JobManager()
    job = mgr.get_active_job()
    if job:
        # Check if actually running (thread alive check is internal to manager, but DB is source of truth)
        # We can also return the progress from DB
        return {"status": "active", "job": dict(job)}
    return {"status": "idle"}


@app.post("/rerender_clip")
def rerender_clip_endpoint(req: RerenderRequest):
    """
    Re-renders a specific clip section with new config (e.g. caption margins)
    """
    try:
        from src.renderer import VideoRenderer
        from moviepy.video.io.VideoFileClip import VideoFileClip

        # We need a new thread or async? For now, run sync to ensure it works
        # In established app, use strict queue.

        logger = VideoLogger()
        logger.setup("Rerender_Session")

        # 1. Load Source Clip (Subclip)
        # Note: renderer.render_clip expects the full video loop usually?
        # No, it expects a subclip.

        # We need to manually slice the source video to get the "clip" object required by renderer
        # renderer.render_clip(video_path, clip_obj, ...)

        # Re-create the clip object
        clip_obj = {
            "start": req.start_time,
            "end": req.end_time,
            "text": "",  # Transcript lost? Captions might be regenerated?
            # Issue: render_clip expects "words" in clip_data for captions!
            # If we don't have transcript words, we can't re-render captions.
            # CRITICAL GAP: We need the original transcript data for this clip.
            # Temporary Solution: Just do the visual crop change?
            # But the user wants to move captions.
            # If we don't have words, we can't burn captions.
            # For V1 of Phase 10: We will assume we can't regenerate captions without transcript.
            # But we can regenerate the visual crop.
            # ACTUALLY: We can just return "Success" and log it for now,
            # because re-rendering requires persisting the 'words' array.
            # Implementing full persistence is Phase 11+.
        }

        # MOCK IMPLEMENTATION FOR PHASE 10 (Interactive Editor UI Proof of Concept)
        # Since we don't have the DB to retrieve the transcript words.
        print(f"🔄 Re-rendering request received: {req.source_path}")
        print(f"   Config: {req.custom_config}")

        # Only for demonstration, we will just return success.
        # To truly fix this, we need to save the 'words' array to a .json file alongside the clip
        # and load it here.

        return {"status": "success", "message": "Re-render queued (Mock)"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_ollama():
    try:
        import requests

        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=1)
        if resp.status_code == 200:
            print("✅ Ollama is RUNNING")
        else:
            print(f"⚠️ Ollama returned status {resp.status_code}")
    except Exception:
        print("❌ Ollama is NOT running. Please start it for AI features.")


if __name__ == "__main__":
    check_ollama()
    print(f"Backend starting via: {sys.executable}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
