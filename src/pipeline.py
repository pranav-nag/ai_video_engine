import os
import time
import threading
import gc
from dotenv import load_dotenv

# Import our AI Modules
from src.ingest_transcribe import VideoIngestor, Transcriber
from src.analyzer import analyze_transcript, ensure_ollama_running
from src.cropper import SmartCropper
from src.renderer import VideoRenderer
from src.logger import VideoLogger
from src.caption_enhancer import CaptionEnhancer
from src.layout_engine import LayoutEngine

# Load Environment Variables
load_dotenv()


def run_ai_pipeline(
    url,
    style,
    res,
    min_sec,
    max_sec,
    start_time,
    end_time,
    caption_size,
    caption_pos,
    focus_region,
    output_bitrate,
    output_resolution,
    content_type,
    use_b_roll=True,
    use_split_screen=True,
    custom_config=None,
    logger=None,
    progress_callback=None,
    cancel_event=None,
):
    """
    Executes the full AI Video generation pipeline.
    Decoupled from Flet UI.
    """
    if not logger:
        logger = VideoLogger()
        logger.setup("Headless_Pipeline")

    # Lower process priority to prevent UI freeze
    try:
        import psutil

        p = psutil.Process(os.getpid())
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        logger.log("📉 Process priority set to BELOW_NORMAL to prevent UI lag.", "INFO")
    except Exception as e:
        logger.log(f"⚠️ Could not set process priority: {e}", "WARNING")

    if not cancel_event:
        cancel_event = threading.Event()

    start_time_all = time.time()

    def update_progress(p, msg):
        elapsed = time.time() - start_time_all
        eta = 0
        if p > 0.05:  # Only estimate after some progress
            total_est = elapsed / p
            eta = max(0, total_est - elapsed)

        if progress_callback:
            progress_callback(p, msg)

        # Log with ETA
        eta_msg = f" | ETA: {int(eta // 60)}m {int(eta % 60)}s" if eta > 0 else ""
        logger.info(f"[PROGRESS {int(p * 100)}%] {msg}{eta_msg}")

    video_path = None

    try:
        # 0. PRE-FLIGHT CHECKS
        update_progress(0.01, "Checking System Health...")
        try:
            ensure_ollama_running()
        except Exception as e:
            logger.log(f"❌ System Check Failed: {e}", "red")
            raise e

        # 1. DOWNLOAD
        update_progress(0.05, f"Initializing engine ({content_type})...")
        time.sleep(0.1)

        if cancel_event.is_set():
            return

        update_progress(0.1, f"Downloading segment ({res}p)...")
        logger.log(f"🔗 URL: {url}", color="cyan")
        logger.log(f"🎯 Focus Mode: {focus_region.upper()}", color="cyan")

        ingestor = VideoIngestor()
        logger.log(f"⬇️  Starting download from {url}", "blue")  # Log start
        video_path, video_title = ingestor.download(
            url,
            start_time,
            end_time,
            resolution=res,
            logger=logger,
            cancel_event=cancel_event,
        )

        if cancel_event.is_set():
            return
        if not video_path:
            logger.log("❌ Download failed.", color="red")
            return

        if video_title:
            logger.rename_log_file(video_title)

        # 2. TRANSCRIPTION
        update_progress(0.3, "Transcribing Audio (Whisper)...")
        if cancel_event.is_set():
            return

        try:
            transcriber = Transcriber()
            logger.log("🎙️  Initializing Whisper Model...", "purple")
            words = transcriber.transcribe(
                video_path, logger=logger, cancel_event=cancel_event
            )
            print(f"[PIPELINE] Transcription complete. Words: {len(words)}", flush=True)
        except Exception as transcribe_err:
            logger.log(f"❌ Transcription failed: {transcribe_err}", color="red")
            raise

        print("[PIPELINE] Waiting for GPU to stabilize...", flush=True)
        time.sleep(2)

        # CLEANUP after Transcribe
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

        # 3. AI ANALYSIS
        update_progress(0.5, "AI Analyzing for Viral Moments...")
        if cancel_event.is_set():
            return

        # AI analysis progress callback
        def ai_progress(status_msg):
            update_progress(0.55, status_msg)

        try:
            clips, scenes = analyze_transcript(
                words,
                min_sec=min_sec,
                max_sec=max_sec,
                logger=logger,
                video_path=video_path,
                progress_callback=ai_progress,
                content_type=content_type,
            )
        except ConnectionError as e:
            logger.log(str(e), "red")
            raise e
        except Exception as e:
            logger.log(f"❌ Analysis failed: {e}", "red")
            raise e

        # CLEANUP after Analysis
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

        if not clips:
            logger.log("⚠️ No viral clips found.", color="orange")
            update_progress(1.0, "Done (No Clips Found)")
            return

        if cancel_event.is_set():
            return

        # 4. SMART CROP & LAYOUT ANALYSIS
        update_progress(0.65, "Analyzing Video Layout (Solo vs Podcast)...")
        if cancel_event.is_set():
            return

        if cancel_event.is_set():
            return

        # Determine Layout Mode (Active Speaker vs Split Screen)
        layout_mode = "active_speaker"
        layout_coords = None

        if use_split_screen:
            layout_engine = LayoutEngine()
            layout_result = layout_engine.analyze_layout(video_path, logger=logger)
            layout_mode = layout_result["layout_mode"]
            layout_coords = layout_result["coords"]
        else:
            logger.log("⚙️ Split-Screen disabled by user preference.", "INFO")

        update_progress(0.7, "Analyzing Face Movement...")

        update_progress(0.7, "Analyzing Face Movement...")
        if cancel_event.is_set():
            return

        cropper = SmartCropper()

        def crop_progress(p):
            val = 0.7 + (p * 0.15)
            update_progress(val, f"Smart Cropping: {int(p * 100)}%")

        crop_map, w, h, face_map = cropper.analyze_video(
            video_path,
            progress_callback=crop_progress,
            logger=logger,
            focus_region=focus_region,
            scene_boundaries=scenes,
        )
        logger.log(
            f"📐 Smart Crop Analysis Complete. Scene count: {len(scenes)}", "cyan"
        )

        # CLEANUP after Crop
        gc.collect()

        if cancel_event.is_set():
            return

        # 5. RENDERING
        update_progress(0.85, f"Rendering {len(clips)} Clips...")
        renderer = VideoRenderer()
        output_folder = os.path.join(os.getcwd(), "output")
        os.makedirs(output_folder, exist_ok=True)

        import re

        def sanitize_filename(name):
            return re.sub(r'[<>:"/\\|?*]', "_", name)

        from datetime import datetime

        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        from src.logger import UIProglog

        generated_clips = []

        for i, clip in enumerate(clips):
            if cancel_event.is_set():
                break

            safe_title = sanitize_filename(video_title[:40])
            clip_start_sec = int(clip["start"])
            clip_end_sec = int(clip["end"])
            clip_duration = clip_end_sec - clip_start_sec
            start_fmt = f"{clip_start_sec // 60:02d}m{clip_start_sec % 60:02d}s"

            clip_filename = (
                f"{safe_title.replace(' ', '_')}_{batch_timestamp}_"
                f"Clip{i + 1}_Start{start_fmt}_Dur{clip_duration}s_{style}.mp4"
            )
            output_path = os.path.join(output_folder, clip_filename)

            clip["words"] = [
                w
                for w in words
                if w["start"] >= clip["start"] and w["end"] <= clip["end"]
            ]

            # --- VISUAL ENHANCEMENT ---
            # Apply colored keywords and emojis
            enhancer = CaptionEnhancer()
            clip["words"] = enhancer.enhance_transcript(clip["words"])

            logger.log(
                f"🎨 Enhanced captions for Clip {i + 1} (Power Words & Emojis)", "INFO"
            )

            # Validate that the clip has valid start/end times
            if clip["end"] - clip["start"] < 1.0:
                logger.log(
                    f"⚠️ Clip {i + 1} is too short ({clip_duration:.1f}s), skipping.",
                    "orange",
                )
                continue

            logger.log(
                f"🎞️ Rendering Clip {i + 1} (Score: {clip.get('score', 0):.1f})...",
                color="blue",
            )

            # Simple progress adapter for Proglog
            # We can't use FletProglog directly if it depends on UI controls,
            # but we can pass a simple lambda to it if it accepts a callback.
            # Looking at FletProglog in logger.py, it calls ui_callback(percentage, msg).
            # We can pass our update_progress here.

            class SocketProglog(UIProglog):
                def __init__(self, callback):
                    super().__init__(ui_callback=callback)

            result = renderer.render_clip(
                video_path,
                clip,
                crop_map,
                output_path,
                face_presence_map=face_map,
                style_name=style,
                font_size=caption_size,
                position=caption_pos,
                output_bitrate=output_bitrate,
                output_resolution=output_resolution,
                custom_config=custom_config,
                logger=logger,
                proglog_logger=SocketProglog(
                    callback=lambda p, m: update_progress(
                        0.5 + ((i + (p if p else 0)) / len(clips) * 0.5),
                        {
                            "phase": "Rendering Engines",
                            "phase_progress": p if p else 0,
                            "text": f"Rendering Clip {i + 1} of {len(clips)}...",
                        },
                    )
                ),
                layout_mode=layout_mode,
                layout_coords=layout_coords,
                use_b_roll=use_b_roll,
            )

            # Unpack the result from renderer
            if isinstance(result, tuple):
                output_path, thumbnail_path = result
            else:
                output_path = result
                thumbnail_path = ""  # Fallback

            # Broadcast the new clip availability to Frontend
            # Format: CLIP_READY:path|title|thumbnail|score
            clip_score = clip.get("score", 0)
            update_progress(
                0.8 + ((i + 1) / len(clips) * 0.2),
                f"CLIP_READY:{output_path}|Clip {i + 1}|{thumbnail_path}|{clip_score}|{video_path}|{clip['start']}|{clip['end']}",
            )

        if not cancel_event.is_set():
            update_progress(1.0, "Done!")
            logger.log("🎉 Process Complete!", color="green")
            return generated_clips
        else:
            logger.log("🛑 Process Cancelled.", color="red")
            return None

    except Exception as e:
        import traceback

        logger.error(str(e))
        logger.log(f"❌ Error: {str(e)}", color="red")
        print(traceback.format_exc())
        raise

    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass

        try:
            from src.cleanup import cleanup_temp_files

            cleanup_temp_files()
        except Exception:
            pass
