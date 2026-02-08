import flet as ft
import threading
import os
import sys
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


# Redirect terminal output to UI
class StreamToLogger:
    def __init__(self, log_list_control):
        self.log_list = log_list_control
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)

        # Add to UI (Clean up newlines)
        clean_msg = message.strip()
        if clean_msg:
            try:
                # Color Logic
                color = ft.colors.WHITE
                if (
                    "❌" in clean_msg
                    or "Error" in clean_msg
                    or "Exception" in clean_msg
                ):
                    color = ft.colors.RED_400
                elif "⚠️" in clean_msg or "Warning" in clean_msg:
                    color = ft.colors.ORANGE_400
                elif "✅" in clean_msg or "Success" in clean_msg:
                    color = ft.colors.GREEN_400
                elif "Downloading" in clean_msg or "🔗" in clean_msg:
                    color = ft.colors.CYAN_300
                elif "🧠" in clean_msg:
                    color = ft.colors.PURPLE_300

                self.log_list.controls.append(
                    ft.Text(
                        clean_msg,
                        font_family="Consolas",
                        size=12,
                        color=color,
                        selectable=True,
                    )
                )
                self.log_list.update()
                self.log_list.scroll_to(offset=-1, duration=50)
            except:
                pass

    def flush(self):
        self.terminal.flush()


def main(page: ft.Page):
    # --- 1. App Configuration ---
    page.title = "AI Video Engine PRO - Co-Pilot Edition"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1600  # Wider for new layout
    page.window_height = 1000
    page.padding = 0
    page.bgcolor = ft.colors.BLACK

    is_processing = False
    cancel_event = threading.Event()
    video_logger = VideoLogger()

    # State for Duration
    video_duration_seconds = 300  # Default 5 min

    # --- 2. UI Components ---

    # Logs (Defined early for redirection)
    log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True)

    # Redirect Streams
    sys.stdout = StreamToLogger(log_list)
    sys.stderr = StreamToLogger(log_list)

    # 2.1 Left Panel Controls (The "Cockpit")

    # URL Input with Action
    url_input = ft.TextField(
        label="Video URL (YouTube)",
        hint_text="Paste link and press Enter...",
        text_size=15,
        prefix_icon=ft.icons.LINK,
        expand=True,
        content_padding=15,
        border_radius=10,
        filled=True,
        bgcolor=ft.colors.BLACK12,
    )

    fetch_info_btn = ft.IconButton(
        icon=ft.icons.REFRESH,
        tooltip="Fetch Video Info",
        icon_color=ft.colors.BLUE_400,
        icon_size=24,
    )

    video_info_text = ft.Text(
        "No video loaded", size=13, color=ft.colors.GREY_300, italic=True
    )

    # Tabs for Settings

    # Tab 1: Input & Analysis
    res_dropdown = ft.Dropdown(
        label="Quality / Resolution",
        options=[
            ft.dropdown.Option("360", "360p (Fastest/Proxy)"),
            ft.dropdown.Option("720", "720p (Balanced)"),
            ft.dropdown.Option("1080", "1080p (Production)"),
        ],
        value="1080",
        text_size=14,
        border_radius=10,
        border_color=ft.colors.GREY_700,
    )

    analysis_start = ft.TextField(
        label="Start",
        value="0:00",
        expand=1,
        text_size=14,
        border_radius=10,
        filled=True,
        bgcolor=ft.colors.BLACK12,
    )

    analysis_end = ft.TextField(
        label="End",
        value="5:00",
        expand=1,
        text_size=14,
        border_radius=10,
        filled=True,
        bgcolor=ft.colors.BLACK12,
    )

    # Source Video Segment Slider
    source_range_slider = ft.RangeSlider(
        min=0,
        max=300,  # Will be updated dynamically
        start_value=0,
        end_value=300,
        label="{value}s",
        active_color=ft.colors.CYAN_400,
        inactive_color=ft.colors.GREY_800,
    )

    quick_select_chips = ft.Row(
        [
            ft.Chip(
                label=ft.Text("Full Video"),
                label_style=ft.TextStyle(color=ft.colors.WHITE),
                bgcolor=ft.colors.BLUE_900,
                on_click=lambda e: set_range(0, video_duration_seconds),
            ),
            ft.Chip(
                label=ft.Text("First 60s"),
                label_style=ft.TextStyle(color=ft.colors.WHITE),
                bgcolor=ft.colors.GREY_800,
                on_click=lambda e: set_range(0, 60),
            ),
            ft.Chip(
                label=ft.Text("Last 60s"),
                label_style=ft.TextStyle(color=ft.colors.WHITE),
                bgcolor=ft.colors.GREY_800,
                on_click=lambda e: set_range(
                    max(0, video_duration_seconds - 60), video_duration_seconds
                ),
            ),
        ],
        spacing=10,
    )

    # Tab 2: Style (Co-pilot)
    style_dropdown = ft.Dropdown(
        label="Caption Style",
        options=[
            ft.dropdown.Option("Hormozi", "Hormozi (Bold/Yellow)"),
            ft.dropdown.Option("Minimal", "Minimal (Clean/White)"),
            ft.dropdown.Option("Neon", "Neon (Glow/Cyan)"),
            ft.dropdown.Option("Boxed", "Boxed (Black Background)"),
        ],
        value="Hormozi",
        text_size=14,
        border_radius=10,
        border_color=ft.colors.GREY_700,
    )

    focus_dropdown = ft.Dropdown(
        label="Focus Region (Speaker)",
        options=[
            ft.dropdown.Option("auto", "Auto (Smart Weighted)"),
            ft.dropdown.Option("center", "Force Center"),
            ft.dropdown.Option("left", "Force Left (Speaker A)"),
            ft.dropdown.Option("right", "Force Right (Speaker B)"),
        ],
        value="auto",
        text_size=14,
        border_radius=10,
        border_color=ft.colors.GREY_700,
    )

    caption_pos_dropdown = ft.Dropdown(
        label="Position",
        options=[
            ft.dropdown.Option("center", "Center (Impact)"),
            ft.dropdown.Option("bottom", "Bottom (Standard)"),
            ft.dropdown.Option("top", "Top (Experimental)"),
        ],
        value="center",
        text_size=14,
        border_radius=10,
        border_color=ft.colors.GREY_700,
    )

    caption_size_slider = ft.Slider(
        min=20,
        max=100,
        value=60,
        label="Font Size: {value}px",
        active_color=ft.colors.PURPLE_400,
    )

    # Tab 3: AI & Output
    duration_slider = ft.RangeSlider(
        min=5,
        max=90,
        start_value=15,
        end_value=60,
        divisions=17,
        label="{value}s",
        active_color=ft.colors.GREEN_400,
        inactive_color=ft.colors.GREY_700,
    )

    duration_label = ft.Text(
        "Target Length: 15s - 60s", size=13, color=ft.colors.GREEN_400
    )

    # Output Quality Controls
    output_bitrate_dropdown = ft.Dropdown(
        label="Output Bitrate",
        options=[
            ft.dropdown.Option("auto", "Auto (High Quality)"),
            ft.dropdown.Option("10000k", "10 Mbps (Good)"),
            ft.dropdown.Option("20000k", "20 Mbps (Great)"),
            ft.dropdown.Option("50000k", "50 Mbps (4K/Max)"),
        ],
        value="auto",
        text_size=14,
        border_radius=10,
        border_color=ft.colors.GREY_700,
    )

    output_resolution_dropdown = ft.Dropdown(
        label="Output Resolution",
        options=[
            ft.dropdown.Option("1080x1920", "9:16 (1080x1920) HD"),
            ft.dropdown.Option("720x1280", "9:16 (720x1280) SD"),
            ft.dropdown.Option("source", "Match Source Quality"),
        ],
        value="1080x1920",
        text_size=14,
        border_radius=10,
        border_color=ft.colors.GREY_700,
    )

    # Action Area
    progress_bar = ft.ProgressBar(
        width=None,
        color=ft.colors.BLUE_400,
        bgcolor=ft.colors.GREY_800,
        value=0,
        height=8,
        border_radius=4,
    )
    progress_text = ft.Text("Ready", size=12, italic=True, color=ft.colors.WHITE70)

    cancel_btn = ft.ElevatedButton(
        "STOP 🛑",
        style=ft.ButtonStyle(
            bgcolor=ft.colors.RED_600,
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
        disabled=True,
    )

    process_btn = ft.ElevatedButton(
        "GENERATE VIRAL CLIPS 🚀",
        style=ft.ButtonStyle(
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
        width=None,  # Expand
    )

    # Logs
    # log_list was defined early for redirection
    # log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True)

    # 2.2 Right Panel (Results Library) - Compact
    gallery_grid = ft.GridView(
        expand=True,
        runs_count=1,  # Single column for compact view? or 2 if expanded
        max_extent=300,
        child_aspect_ratio=0.56,  # 9:16 approx
        spacing=10,
        run_spacing=10,
        visible=False,
    )

    gallery_empty_state = ft.Container(
        content=ft.Column(
            [
                ft.Icon(
                    ft.icons.VIDEO_LIBRARY_OUTLINED, size=64, color=ft.colors.GREY_800
                ),
                ft.Text("Your viral clips will appear here.", color=ft.colors.GREY_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
    )

    # --- 3. Logic & Callbacks ---

    def log_to_ui(message, color=ft.colors.WHITE):
        log_list.controls.append(
            ft.Text(
                f"[{datetime.now().strftime('%H:%M:%S')}] {message}",
                color=color,
                size=12,
                font_family="JetBrains Mono, Consolas",
            )
        )
        page.update()

    def update_progress(val, text):
        progress_bar.value = val
        progress_text.value = text
        page.update()

    def format_seconds(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{int(h)}:{int(m):02d}:{int(s):02d}"
        return f"{int(m)}:{int(s):02d}"

    def set_range(start, end):
        # Update Slider
        source_range_slider.start_value = float(start)
        source_range_slider.end_value = min(float(end), source_range_slider.max)
        # Update Text
        analysis_start.value = format_seconds(source_range_slider.start_value)
        analysis_end.value = format_seconds(source_range_slider.end_value)
        page.update()

    def on_source_slider_change(e):
        analysis_start.value = format_seconds(e.control.start_value)
        analysis_end.value = format_seconds(e.control.end_value)
        page.update()

    source_range_slider.on_change = on_source_slider_change

    def fetch_video_metadata(e):
        url = url_input.value
        if not url:
            return

        url_input.read_only = True
        video_info_text.value = "Fetching metadata..."
        page.update()

        def _fetch():
            nonlocal video_duration_seconds
            try:
                ingestor = VideoIngestor()
                dur, title = ingestor.get_video_info(url)

                if dur > 0:
                    video_duration_seconds = int(dur)
                    fmt_dur = format_seconds(video_duration_seconds)

                    # Update UI on main thread
                    video_info_text.value = f"🎬 {title[:40]}... | ⏱️ {fmt_dur}"

                    # Update Slider
                    source_range_slider.max = float(video_duration_seconds)
                    source_range_slider.end_value = float(video_duration_seconds)
                    source_range_slider.divisions = int(video_duration_seconds)

                    analysis_end.value = fmt_dur
                    video_logger.log(f"✅ Metadata fetched: {fmt_dur}", ft.colors.GREEN)
                else:
                    video_info_text.value = "Could not fetch duration (Live stream?)"

            except Exception as e:
                video_info_text.value = "Error fetching metadata"

            url_input.read_only = False
            page.update()

        # Run in thread to not block UI
        threading.Thread(target=_fetch, daemon=True).start()

    fetch_info_btn.on_click = fetch_video_metadata
    url_input.on_submit = fetch_video_metadata

    def on_slider_change(e):
        duration_label.value = f"Target Length: {int(e.control.start_value)}s - {int(e.control.end_value)}s"
        page.update()

    duration_slider.on_change = on_slider_change

    # --- 4. Pipeline Execution ---
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
    ):
        nonlocal is_processing

        try:
            video_logger.setup("Session_Start", ui_callback=log_to_ui)

            # 1. DOWNLOAD
            update_progress(0.05, "Initializing engine...")
            time.sleep(0.1)

            if cancel_event.is_set():
                return

            update_progress(0.1, f"Downloading segment ({res}p)...")
            video_logger.log(f"🔗 URL: {url}", ft.colors.BLUE_200)
            video_logger.log(
                f"🎯 Focus Mode: {focus_region.upper()}", ft.colors.CYAN_200
            )

            ingestor = VideoIngestor()
            video_path, video_title = ingestor.download(
                url, start_time, end_time, resolution=res, logger=video_logger
            )

            if cancel_event.is_set():
                return
            if not video_path:
                video_logger.log("❌ Download failed.", ft.colors.RED)
                return

            if video_title:
                video_logger.rename_log_file(video_title)

            # 2. TRANSCRIPTION
            update_progress(0.3, "Transcribing Audio (Whisper)...")
            if cancel_event.is_set():
                return

            transcriber = Transcriber()
            words = transcriber.transcribe(video_path, logger=video_logger)

            # 3. AI ANALYSIS
            update_progress(0.5, "AI Analyzing for Viral Moments...")
            if cancel_event.is_set():
                return

            formatted_text = format_transcript_with_time(words)
            clips = analyze_transcript(
                formatted_text,
                min_sec=min_sec,
                max_sec=max_sec,
                logger=video_logger,
                video_path=video_path,
            )
            video_logger.capture_ollama_logs()

            if cancel_event.is_set():
                return
            if not clips:
                video_logger.log("⚠️ No clips found.", ft.colors.ORANGE)
                return

            # 4. SMART CROP (Optimized)
            update_progress(0.7, "Analyzing Face Movement...")
            if cancel_event.is_set():
                return

            cropper = SmartCropper()
            crop_start_time = time.time()

            def crop_progress(p):
                # Check cancel inside callback if possible?
                # Hard to return from callback to stop parent.
                # Just rely on outer checks.
                elapsed = time.time() - crop_start_time
                val = 0.7 + (p * 0.15)
                # Simple ETA
                if p > 0.1:
                    total = elapsed / p
                    rem = total - elapsed
                    eta = f"{int(rem)}s"
                else:
                    eta = "..."
                update_progress(val, f"Smart Cropping: {int(p * 100)}% (ETA: {eta})")

            crop_map, w, h = cropper.analyze_video(
                video_path,
                progress_callback=crop_progress,
                logger=video_logger,
                focus_region=focus_region,
            )

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

            for i, clip in enumerate(clips):
                if cancel_event.is_set():
                    break

                safe_title = sanitize_filename(video_title[:30])
                clip_filename = (
                    f"{safe_title.replace(' ', '_')}_Clip_{i + 1}_{style}.mp4"
                )
                output_path = os.path.join(output_folder, clip_filename)

                clip["words"] = [
                    w
                    for w in words
                    if w["start"] >= clip["start"] and w["end"] <= clip["end"]
                ]

                video_logger.log(f"🎞️ Rendering Clip {i + 1}...", ft.colors.BLUE_200)
                renderer.render_clip(
                    video_path,
                    clip,
                    crop_map,
                    output_path,
                    style_name=style,
                    font_size=caption_size,
                    position=caption_pos,
                    output_bitrate=output_bitrate,
                    output_resolution=output_resolution,
                    logger=video_logger,
                )

                # GALLERY UPDATE
                gallery_empty_state.visible = False
                gallery_grid.visible = True
                gallery_grid.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        ft.icons.PLAY_CIRCLE_FILLED,
                                        size=40,
                                        color=ft.colors.WHITE70,
                                    ),
                                    alignment=ft.Alignment(0, 0),
                                    height=150,
                                    bgcolor=ft.colors.BLACK54,
                                    border_radius=8,
                                ),
                                ft.Text(
                                    clip["hook"],
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    f"⭐ {clip['score']}% | {clip['end'] - clip['start']:.1f}s",
                                    size=10,
                                    color=ft.colors.AMBER,
                                ),
                            ],
                            spacing=5,
                        ),
                        bgcolor=ft.colors.GREY_900,
                        padding=10,
                        border_radius=10,
                    )
                )
                page.update()

            if not cancel_event.is_set():
                update_progress(1.0, "Done!")
                video_logger.log("🎉 Process Complete!", ft.colors.GREEN)
            else:
                video_logger.log("🛑 Process Cancelled.", ft.colors.RED)

        except Exception as e:
            video_logger.error(str(e))
            video_logger.log(f"❌ Error: {str(e)}", ft.colors.RED)

        finally:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass

            # Cleanup
            try:
                from src.cleanup import cleanup_temp_files

                cleanup_temp_files()
            except:
                pass

            video_logger.close()
            is_processing = False
            process_btn.disabled = False
            process_btn.text = "GENERATE VIRAL CLIPS 🚀"
            cancel_btn.disabled = True
            update_progress(0, "Ready")

    def on_cancel_click(e):
        if is_processing:
            cancel_event.set()
            video_logger.log("🛑 Cancellation Requested...", ft.colors.RED)
            cancel_btn.disabled = True
            page.update()

    cancel_btn.on_click = on_cancel_click

    def on_start_click(e):
        if not url_input.value:
            url_input.error_text = "Required"
            page.update()
            return

        cancel_event.clear()
        process_btn.disabled = True
        process_btn.text = "Processing..."
        cancel_btn.disabled = False
        gallery_grid.controls.clear()
        gallery_grid.visible = False
        gallery_empty_state.visible = True

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
                int(caption_size_slider.value),
                caption_pos_dropdown.value,
                focus_dropdown.value,
                output_bitrate_dropdown.value,
                output_resolution_dropdown.value,
            ),
            daemon=True,
        ).start()

    process_btn.on_click = on_start_click

    # --- 5. Layout Assembly ---

    settings_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Input",
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Source Video", weight=ft.FontWeight.BOLD),
                            res_dropdown,
                            ft.Divider(color=ft.colors.TRANSPARENT, height=5),
                            ft.Text(
                                "Analyze Segment", size=12, color=ft.colors.GREY_400
                            ),
                            ft.Row([analysis_start, analysis_end], spacing=10),
                            source_range_slider,
                            quick_select_chips,
                            ft.Divider(color=ft.colors.TRANSPARENT, height=10),
                            ft.Text("Duration Info", size=12, color=ft.colors.GREY_400),
                            video_info_text,
                        ],
                        spacing=15,
                    ),
                    padding=20,
                ),
            ),
            ft.Tab(
                text="Co-Pilot Styles",
                content=ft.Container(
                    content=ft.Column(
                        [
                            style_dropdown,
                            focus_dropdown,
                            caption_pos_dropdown,
                            ft.Text("Caption Size"),
                            caption_size_slider,
                        ],
                        spacing=15,
                    ),
                    padding=20,
                ),
            ),
            ft.Tab(
                text="AI & Target",
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Clip Length", weight=ft.FontWeight.BOLD),
                            duration_label,
                            duration_slider,
                            ft.Divider(),
                            ft.Text("Output Quality", weight=ft.FontWeight.BOLD),
                            output_bitrate_dropdown,
                            output_resolution_dropdown,
                            ft.Divider(),
                            ft.Text(
                                "Advanced: Scene Detect (Coming Soon)",
                                color=ft.colors.GREY_600,
                            ),
                        ],
                        spacing=15,
                    ),
                    padding=20,
                ),
            ),
        ],
        expand=True,
    )

    # --- 5. Layout Assembly ---

    # 5.1 Sidebar (Left Panel - Controls)
    sidebar = ft.Container(
        content=ft.Column(
            [
                # Header
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.AUTO_AWESOME, color=ft.colors.BLUE_400, size=32
                        ),
                        ft.Text("AI ENGINE PRO", size=26, weight=ft.FontWeight.W_900),
                    ]
                ),
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                # URL & Fetch
                ft.Row(
                    [url_input, fetch_info_btn],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                # Settings Tabs
                ft.Container(
                    content=settings_tabs,
                    height=450,  # Slightly taller
                    bgcolor=ft.colors.GREY_900,
                    border_radius=12,
                    padding=10,
                ),
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                # Actions
                ft.Row(
                    [
                        ft.Container(process_btn, expand=True),
                        cancel_btn,
                    ],
                    spacing=10,
                ),
                ft.Column([progress_bar, progress_text], spacing=5),
            ],
            spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO,  # Allow scrolling if height small
        ),
        width=500,  # Narrower for better balance
        padding=30,
        bgcolor=ft.colors.GREY_900,
        border=ft.border.only(right=ft.border.BorderSide(1, ft.colors.BLACK12)),
    )

    # 5.2 Right Panel (Logs + Gallery)
    right_panel = ft.Container(
        content=ft.Column(
            [
                # Top: Live Logs
                ft.Text("Live Intelligence & Logs", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=log_list,
                    height=300,  # Fixed height for logs, but could be flexible
                    bgcolor=ft.colors.BLACK87,
                    border=ft.border.all(1, ft.colors.GREY_800),
                    border_radius=8,
                    padding=10,
                ),
                ft.Divider(),
                # Bottom: Gallery
                ft.Row(
                    [
                        ft.Text("Project Library", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("Output: ./output", size=12, color=ft.colors.GREY_500),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=ft.Stack([gallery_empty_state, gallery_grid], expand=True),
                    expand=True,  # Takes rest of the space
                    bgcolor=ft.colors.TRANSPARENT,
                ),
            ],
            spacing=15,
            expand=True,
        ),
        padding=25,
        expand=True,  # Takes remaining page width
        bgcolor=ft.colors.BLACK,
        # Create a subtle gradient or pattern background if supported, else just black
    )

    # Add to Page
    page.add(ft.Row([sidebar, right_panel], expand=True, spacing=0))


if __name__ == "__main__":
    ft.app(target=main)
