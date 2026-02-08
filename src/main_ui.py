import flet as ft
import threading
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Import our AI Modules
from src.ingest_transcribe import VideoIngestor, Transcriber
from src.analyzer import analyze_transcript, format_transcript_with_time
from src.cropper import SmartCropper
from src.renderer import VideoRenderer
from src.logger import VideoLogger

# Load Environment Variables
load_dotenv()


def main(page: ft.Page):
    # --- 1. App Configuration ---
    page.title = "AI Video Engine PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1400
    page.window_height = 950
    page.padding = 0
    page.bgcolor = ft.Colors.BLACK

    is_processing = False
    video_logger = VideoLogger()

    # --- 2. UI Components ---

    # 2.1 Sidebar Components
    url_input = ft.TextField(
        label="Video URL (YouTube)",
        hint_text="e.g. youtube.com/watch?v=...",
        border_color=ft.Colors.BLUE_400,
        text_size=14,
        prefix_icon=ft.Icons.LINK,
    )

    res_dropdown = ft.Dropdown(
        label="Quality / Resolution",
        options=[
            ft.dropdown.Option("360", "360p (Ultra Fast/Low VRAM)"),
            ft.dropdown.Option("720", "720p (High Performance)"),
            ft.dropdown.Option("1080", "1080p (Production Quality)"),
        ],
        value="1080",
        border_color=ft.Colors.YELLOW_700,
    )

    analysis_start = ft.TextField(
        label="From (0:00)",
        value="0:00",
        width=135,
        border_color=ft.Colors.AMBER_400,
    )

    analysis_end = ft.TextField(
        label="To (5:00)",
        value="5:00",
        width=135,
        border_color=ft.Colors.AMBER_400,
    )

    style_dropdown = ft.Dropdown(
        label="Caption Style",
        options=[
            ft.dropdown.Option("Hormozi", "Hormozi (Bold/Yellow)"),
            ft.dropdown.Option("Minimal", "Minimal (Clean/White)"),
            ft.dropdown.Option("Neon", "Neon (Glow/Cyan)"),
        ],
        value="Hormozi",
        border_color=ft.Colors.PURPLE_400,
    )

    duration_slider = ft.RangeSlider(
        min=5,
        max=90,
        start_value=15,
        end_value=60,
        divisions=17,
        label="{value}s",
        active_color=ft.Colors.GREEN_400,
        inactive_color=ft.Colors.GREY_700,
    )

    duration_label = ft.Text(
        "AI Target Length: 15s - 60s", size=13, color=ft.Colors.GREEN_400
    )

    # 2.2 Progress Indicators
    progress_bar = ft.ProgressBar(
        width=280, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.GREY_800, value=0
    )
    progress_text = ft.Text("Idle", size=11, italic=True, color=ft.Colors.GREY_500)

    process_btn = ft.ElevatedButton(
        "Generate Clips 🚀",
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        height=55,
        width=280,
    )

    # 2.3 Logs & Gallery
    log_list = ft.ListView(expand=True, spacing=4, auto_scroll=True)

    gallery_grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=350,
        child_aspect_ratio=0.6,
        spacing=20,
        run_spacing=20,
    )

    # --- 3. Logic & Callbacks ---

    def log_to_ui(message, color=ft.Colors.WHITE):
        log_list.controls.append(
            ft.Text(
                f"[{datetime.now().strftime('%H:%M:%S')}] {message}",
                color=color,
                size=13,
                font_family="JetBrains Mono, Consolas",
            )
        )
        page.update()

    def update_progress(val, text):
        progress_bar.value = val
        progress_text.value = text
        page.update()

    def on_slider_change(e):
        duration_label.value = f"AI Target Length: {int(e.control.start_value)}s - {int(e.control.end_value)}s"
        page.update()

    duration_slider.on_change = on_slider_change

    # --- 4. Pipeline Execution ---
    def run_ai_pipeline(url, style, res, min_sec, max_sec, start_time, end_time):
        nonlocal is_processing
        is_processing = True
        process_btn.disabled = True
        gallery_grid.controls.clear()
        video_path = None

        video_logger.setup("Session_Start", ui_callback=log_to_ui)

        try:
            # 1. DOWNLOAD
            update_progress(0.1, "Downloading high-speed segment...")
            video_logger.log(f"🔗 URL: {url} | Res: {res}p", ft.Colors.BLUE_200)

            ingestor = VideoIngestor()
            video_path, video_title = ingestor.download(
                url, start_time, end_time, resolution=res
            )

            if not video_path:
                video_logger.log("❌ Download failed.", ft.Colors.RED)
                return

            if video_title:
                video_logger.rename_log_file(video_title)
                video_logger.log(f"🎬 Video: {video_title}", ft.Colors.WHITE)

            # 2. TRANSCRIPTION
            update_progress(0.3, "Transcribing Audio (Whisper)...")
            video_logger.log("🎙️ Extracting word-level timestamps...", ft.Colors.CYAN)
            transcriber = Transcriber()
            words = transcriber.transcribe(video_path)

            # 3. AI ANALYSIS
            update_progress(0.5, "AI Analyzing for Viral Moments...")
            video_logger.log("🧠 Consulting Llama 3.2...", ft.Colors.PURPLE)
            formatted_text = format_transcript_with_time(words)
            clips = analyze_transcript(formatted_text, min_sec=min_sec, max_sec=max_sec)
            video_logger.capture_ollama_logs()

            if not clips:
                video_logger.log(
                    "⚠️ AI found no good clips in this range.", ft.Colors.ORANGE
                )
                return

            # 4. SMART CROP (Optimized multi-threaded)
            update_progress(0.7, "Analyzing Face Movement (MediaPipe)...")
            video_logger.log(
                "📐 Calculating Smart Crop (Cores utilizing...)", ft.Colors.YELLOW
            )
            cropper = SmartCropper()

            crop_start_time = time.time()

            def crop_progress(p):
                elapsed = time.time() - crop_start_time
                if p > 0.05:  # Wait for some samples
                    total_est = elapsed / p
                    remaining = total_est - elapsed
                    min_rem = int(remaining // 60)
                    sec_rem = int(remaining % 60)
                    eta_text = f"ETA: {min_rem}:{sec_rem:02d}"
                else:
                    eta_text = "ETA: Calibrating..."

                val = 0.7 + (p * 0.15)
                update_progress(val, f"Smart Cropping: {int(p * 100)}% | {eta_text}")

            crop_map, w, h = cropper.analyze_video(
                video_path, progress_callback=crop_progress
            )

            # 5. RENDERING
            update_progress(0.85, f"Rendering {len(clips)} Clips (NVENC)...")
            renderer = VideoRenderer()
            # output_folder = r"E:\AI_Video_Engine\output"
            # Use relative path for portability
            output_folder = os.path.join(os.getcwd(), "output")
            os.makedirs(output_folder, exist_ok=True)

            for i, clip in enumerate(clips):
                clip_filename = (
                    f"{video_title[:20].replace(' ', '_')}_Clip_{i + 1}_{style}.mp4"
                )
                output_path = os.path.join(output_folder, clip_filename)

                # Filter words for this segment
                clip["words"] = [
                    w
                    for w in words
                    if w["start"] >= clip["start"] and w["end"] <= clip["end"]
                ]

                video_logger.log(f"🎞️ Rendering Clip {i + 1}...", ft.Colors.BLUE_200)
                renderer.render_clip(
                    video_path, clip, crop_map, output_path, style_name=style
                )

                # GALLERY UI (Fixed Alignment Crash)
                gallery_grid.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.AUTO_AWESOME,
                                        size=40,
                                        color=ft.Colors.WHITE70,
                                    ),
                                    alignment=ft.Alignment(0, 0),  # Fixed
                                    height=200,
                                    bgcolor=ft.Colors.GREY_800,
                                    border_radius=10,
                                ),
                                ft.Text(
                                    clip["hook"],
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.STAR,
                                            size=12,
                                            color=ft.Colors.AMBER,
                                        ),
                                        ft.Text(f"{clip['score']}%", size=11),
                                        ft.VerticalDivider(),
                                        ft.Text(
                                            f"{clip['end'] - clip['start']:.1f}s",
                                            size=11,
                                            color=ft.Colors.GREY_400,
                                        ),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            spacing=8,
                        ),
                        bgcolor=ft.Colors.GREY_900,
                        padding=12,
                        border_radius=15,
                    )
                )
                page.update()

            update_progress(1.0, "Success!")
            video_logger.log("🎉 ALL CLIPS RENDERED SUCCESSFULLY!", ft.Colors.GREEN)

        except Exception as e:
            video_logger.error(str(e))
            video_logger.log(f"❌ Error: {str(e)}", ft.Colors.RED)

        finally:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception:
                    pass

            # --- NEW: Robust Cleanup ---
            try:
                from src.cleanup import cleanup_temp_files

                video_logger.log("🧹 Running cleanup sequence...", ft.Colors.GREY)
                cleanup_temp_files()
            except Exception as e:
                video_logger.log(f"⚠️ Cleanup warning: {e}", ft.Colors.ORANGE)

            video_logger.close()
            is_processing = False
            process_btn.disabled = False
            update_progress(0, "Ready")

    def on_start_click(e):
        if not url_input.value:
            url_input.error_text = "Paste a URL first!"
            page.update()
            return

        threading.Thread(
            target=run_ai_pipeline,
            args=(
                url_input.value,
                style_dropdown.value,
                res_dropdown.value,
                int(duration_slider.start_value),
                int(duration_slider.end_value),
                analysis_start.value,
                analysis_end.value,
            ),
            daemon=True,
        ).start()

    process_btn.on_click = on_start_click

    # --- 5. Layout ---
    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.BLUE_400),
                        ft.Text("AI ENGINE PRO", size=22, weight=ft.FontWeight.BOLD),
                    ]
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Text(
                    "SOURCE & QUALITY",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_500,
                ),
                url_input,
                res_dropdown,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Text(
                    "CLIP SETTINGS",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_500,
                ),
                ft.Row([analysis_start, analysis_end], spacing=10),
                style_dropdown,
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                duration_label,
                duration_slider,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                process_btn,
                ft.Container(height=4),
                progress_bar,
                progress_text,
                ft.Divider(),
                ft.Text(
                    "SESSION LOGS",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_500,
                ),
                ft.Container(
                    content=log_list,
                    expand=True,
                    bgcolor=ft.Colors.BLACK54,
                    border_radius=8,
                    padding=10,
                ),
            ],
            spacing=10,
            expand=True,
        ),
        width=320,
        padding=20,
        bgcolor=ft.Colors.GREY_900,
    )

    main_view = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Project Library", size=28, weight=ft.FontWeight.W_800),
                        ft.VerticalDivider(),
                        ft.Text(
                            "Outputs on E: Drive", size=12, color=ft.Colors.GREY_400
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                gallery_grid,
            ],
            expand=True,
        ),
        padding=30,
        expand=True,
    )

    page.add(ft.Row([sidebar, main_view], expand=True, spacing=0))


if __name__ == "__main__":
    ft.app(target=main)
