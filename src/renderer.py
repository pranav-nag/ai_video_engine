import os
import psutil
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import clips_array
from moviepy import concatenate_videoclips
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.fx import Resize, Crop
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
from dotenv import load_dotenv
from src.fast_caption import SubtitleGenerator
from src.b_roll_manager import BRollManager

# Load Environment Variables
load_dotenv()

# Note: ImageMagick is no longer required since we use .ass subtitles instead of TextClip


class VideoRenderer:
    def __init__(self):
        self.temp_dir = os.getenv("TEMP", r"E:\AI_Video_Engine\temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _set_low_priority(self):
        """Lowers process priority to keep system responsive during heavy rendering."""
        try:
            p = psutil.Process(os.getpid())
            if os.name == "nt":
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            else:
                p.nice(10)  # Nice value 10 is lower priority
        except Exception as e:
            print(f"⚠️ Failed to set low priority: {e}")

    def render_clip(
        self,
        video_path,
        clip_data,
        crop_map,
        output_path,
        face_presence_map=None,  # New Argument
        style_name="Hormozi",
        font_size=60,
        position="center",
        output_bitrate="auto",
        output_resolution="1080x1920",
        logger=None,
        proglog_logger=None,
        custom_config=None,  # NEW
        layout_mode="active_speaker",  # NEW: "active_speaker" or "split_screen"
        layout_coords=None,  # NEW: { "top": (x,y,w,h), "bottom": ... }
        use_b_roll=True,  # NEW
    ):
        # Apply low priority optimization
        self._set_low_priority()
        """
        Renders a single viral clip with:
        1. 9:16 Crop (Dynamic or Split Screen)
        2. ASS Subtitles (Karaoke + Pop)
        3. NVENC Acceleration (RTX 4060)
        4. B-Roll Overlay (when no face detected)
        """
        msg = f"🎬 Starting Render for: {os.path.basename(output_path)} | Style: {style_name} | Font Size: {font_size}px"
        print(msg)
        if logger:
            logger.log(msg, "INFO", "BLUE")

        # 1. Load Video
        try:
            original_clip = VideoFileClip(video_path)
        except Exception as e:
            msg = f"❌ Error: Could not open video {video_path}: {e}"
            print(msg)
            if logger:
                logger.error(msg)
            return

        # 2. Cut the segment
        start_t = clip_data["start"]
        end_t = clip_data["end"]
        duration = end_t - start_t

        # Buffer to avoid audio glitches at boundaries
        clip = original_clip.subclipped(
            max(0, start_t), min(original_clip.duration, end_t)
        )

        # --- B-ROLL LOGIC PRE-CALCULATION ---
        b_roll_intervals = []
        b_roll_clips = []  # To hold clip objects (prevent GC and allow access)

        if face_presence_map:
            # 1. Convert Map to boolean list for this segment
            fps = original_clip.fps or 30.0
            total_frames = int(duration * fps)
            abs_start_frame = int(start_t * fps)

            # Create a boolean array for the clip duration
            face_detected = []
            for i in range(total_frames):
                abs_idx = abs_start_frame + i
                # Default to True (Face Present) if unknown, to be conservative
                face_detected.append(face_presence_map.get(abs_idx, True))

            # 2. Find gaps > 2.0 seconds (approx 60 frames)
            min_gap_frames = int(2.0 * fps)
            current_gap_start = None

            for i, is_face in enumerate(face_detected):
                if not is_face:
                    if current_gap_start is None:
                        current_gap_start = i
                else:
                    if current_gap_start is not None:
                        gap_len = i - current_gap_start
                        if gap_len >= min_gap_frames:
                            # Start/End in seconds relative to clip start
                            gap_start_sec = current_gap_start / fps
                            gap_end_sec = i / fps
                            b_roll_intervals.append((gap_start_sec, gap_end_sec))
                        current_gap_start = None

            # Handle edge case: gap extends to end of clip
            if current_gap_start is not None:
                gap_len = len(face_detected) - current_gap_start
                if gap_len >= min_gap_frames:
                    gap_start_sec = current_gap_start / fps
                    gap_end_sec = len(face_detected) / fps
                    b_roll_intervals.append((gap_start_sec, gap_end_sec))

            # 3. Fetch B-Roll for intervals (No Face)
            if b_roll_intervals and use_b_roll:
                manager = BRollManager()
                # We need to initialize manager once, ideally outside, but here is fine for now
                if (
                    manager.b_roll_files or manager.downloader
                ):  # integrated downloader check
                    msg = f"🎥 Found {len(b_roll_intervals)} 'No Face' segments. Inserting Filler B-Roll..."
                    print(msg)
                    if logger:
                        logger.log(msg, "INFO", "CYAN")

                    for b_start, b_end in b_roll_intervals:
                        b_dur = b_end - b_start
                        b_clip = manager.get_random_b_roll(b_dur)
                        if b_clip:
                            b_roll_clips.append(
                                {
                                    "start": b_start,
                                    "end": b_end,
                                    "clip": b_clip,
                                    "type": "filler",
                                }
                            )

            # 4. KEYWORD B-ROLL (Power Words)
            # Scan transcript for "Power Words" (colored words)
            # We want to overlay B-Roll for 1.5s - 2.0s when these words occur
            if "words" in clip_data and use_b_roll:
                manager = BRollManager()
                for word_info in clip_data["words"]:
                    # Check if word has emphasis color (e.g. YELLOW, GREEN, etc)
                    # The 'color' field comes from caption_enhancer
                    if word_info.get("color") and word_info.get("word"):
                        clean_word = word_info["word"].lower().strip(".,!?")
                        # Heuristic: Only keywords > 3 chars
                        if len(clean_word) > 3:
                            # Avoid overlapping existing B-Roll
                            w_start = word_info["start"]
                            w_end = word_info["end"]
                            # Define B-Roll duration (e.g. 2s or word duration + buffer)
                            b_duration = max(2.0, w_end - w_start + 1.0)

                            # Check overlap with existing b_roll_clips
                            is_overlap = False
                            for br in b_roll_clips:
                                # Simple overlap check
                                if (
                                    w_start < br["end"]
                                    and (w_start + b_duration) > br["start"]
                                ):
                                    is_overlap = True
                                    break

                            if not is_overlap:
                                # Search/Download Stock
                                stock_clip = manager.get_b_roll_for_keyword(
                                    clean_word, b_duration, logger=logger
                                )
                                if stock_clip:
                                    msg = f"🎞️ Inserting Stock Footage for keyword: '{clean_word}'"
                                    print(msg)
                                    if logger:
                                        logger.log(msg, "INFO", "GREEN")
                                    b_roll_clips.append(
                                        {
                                            "start": w_start,
                                            "end": w_start + b_duration,
                                            "clip": stock_clip,
                                            "type": "keyword",
                                        }
                                    )

        # 3. Dynamic Per-Frame 9:16 Crop (follows face)
        src_w = original_clip.w
        src_h = original_clip.h
        crop_w = int(src_h * (9 / 16))
        if crop_w > src_w:
            crop_w = src_w
        fps = original_clip.fps or 30.0
        default_crop_x = (src_w - crop_w) // 2

        # Pre-sort crop_map keys once for efficient interpolation
        _sorted_keys = sorted(crop_map.keys()) if crop_map else []

        # 3.4 CROP & RESIZE (The Magic Sauce)

        # --- SPLIT SCREEN LOGIC ---
        if layout_mode == "split_screen" and layout_coords:
            msg = "⚡ Applying Split-Screen Layout (Podcast Mode)"
            print(msg)
            if logger:
                logger.log(msg, "INFO", "PURPLE")

            # Helper to create a static crop
            def make_crop(coords):
                x, y, w, h = coords
                # Crop
                c = clip.cropped(x1=x, y1=y, width=w, height=h)
                # Resize to target half-height (1080x960)
                # 9:16 = 1080x1920. Half is 1080x960.
                c = c.with_effects([Resize(height=960)])

                # Center crop to 1080 width if needed
                if c.w > 1080:
                    c = c.with_effects([Crop(x_center=c.w / 2, width=1080)])
                # If too narrow, pad? Or resize width?
                # Better: Allow resizing to fill width 1080, then crop height?
                # Let's just resize to width 1080 to be safe
                c = c.with_effects([Resize(width=1080)])
                # Then crop height to 960
                c = c.with_effects([Crop(y_center=c.h / 2, height=960)])
                return c

            top_clip = make_crop(layout_coords["top"])
            bottom_clip = make_crop(layout_coords["bottom"])

            # Stack Vertically
            cropped_clip = clips_array([[top_clip], [bottom_clip]])
            cropped_clip.size = (1080, 1920)  # Enforce

        else:
            # --- SOLO / ACTIVE SPEAKER LOGIC (Legacy) ---

            # Smart Face Tracking
            # Interpolate crop_x for smooth movement
            # _sorted_keys is already defined above
            # fps is already defined above

            def _interpolate_crop_x(abs_t):
                """Find the best crop_x for absolute time t using crop_map."""
                frame_idx = int(abs_t * fps)  # Use the fps derived from original_clip
                # Direct hit
                if frame_idx in crop_map:
                    return crop_map[frame_idx]
                if not _sorted_keys:
                    return default_crop_x
                # Binary search for bracketing keys
                lo, hi = 0, len(_sorted_keys) - 1
                while lo < hi:
                    mid = (lo + hi) // 2
                    if _sorted_keys[mid] < frame_idx:
                        lo = mid + 1
                    else:
                        hi = mid
                # Interpolate between neighbors
                if lo == 0:
                    return crop_map[_sorted_keys[0]]
                if lo >= len(_sorted_keys):
                    return crop_map[_sorted_keys[-1]]
                k_before = _sorted_keys[lo - 1]
                k_after = _sorted_keys[lo]
                if k_after == k_before:
                    return crop_map[k_before]
                ratio = (frame_idx - k_before) / (k_after - k_before)
                val = crop_map[k_before] + ratio * (
                    crop_map[k_after] - crop_map[k_before]
                )
                val = int(val)
                return max(0, min(val, src_w - crop_w))

            def dynamic_crop(get_frame, t):
                """Per-frame crop that follows the face, OR returns B-Roll."""
                # Check B-Roll Overlays first
                for br in b_roll_clips:
                    if br["start"] <= t < br["end"]:
                        # Get frame from B-Roll clip
                        # relative time in b-roll
                        b_t = t - br["start"]
                        try:
                            return br["clip"].get_frame(b_t)
                        except Exception:
                            pass  # Fallback to normal crop if b-roll fails

                # Normal Face Tracking Crop
                frame = get_frame(t)
                abs_t = start_t + t
                cx = _interpolate_crop_x(abs_t)
                # Boundary clamp
                cx = max(0, min(cx, frame.shape[1] - crop_w))
                return frame[:, cx : cx + crop_w]

            cropped_clip = clip.transform(dynamic_crop)
            # MoviePy 2.x: set the output dimensions after transform
            cropped_clip = cropped_clip.with_effects(
                []
            )  # apply empty effects to refresh internals
            cropped_clip.size = (crop_w, src_h)

            # --- PHASE 8: DIGITAL ZOOMS (Safe Mode) ---
            # Only apply if:
            # 1. Clip duration > 5.0s (prevent motion sickness)
            # 2. Not already very zoomed (check resolution? assume 1080 crop is fine)
            # 3. No B-Roll currently covering it (too complex to check here, but dynamic_crop handles it)
            # 4. layout_mode is NOT split_screen
            if duration > 5.0 and layout_mode == "active_speaker":
                try:
                    # Split into 2 halves
                    t_mid = duration * 0.5
                    clip_a = cropped_clip.subclipped(0, t_mid)
                    clip_b = cropped_clip.subclipped(t_mid, duration)

                    # Zoom Part B by 1.15x
                    # We need to scale UP, then center crop back to crop_w x src_h
                    zoom_factor = 1.15
                    new_w = int(crop_w * zoom_factor)
                    new_h = int(src_h * zoom_factor)

                    clip_b_zoomed = clip_b.with_effects(
                        [Resize(width=new_w, height=new_h)]
                    )
                    # Center Crop back to original dimensions
                    clip_b_final = clip_b_zoomed.with_effects(
                        [
                            Crop(
                                x_center=new_w / 2,
                                y_center=new_h / 2,
                                width=crop_w,
                                height=src_h,
                            )
                        ]
                    )

                    # Concatenate with crossfade? No, hard cut is surprisingly better for "punch ins"
                    # But let's verify dimensions match exactly
                    if clip_b_final.size == clip_a.size:
                        msg = f"🔍 Applying Digital Zoom (Punch-in) at {t_mid:.1f}s"
                        print(msg)
                        if logger:
                            logger.log(msg, "INFO")
                        cropped_clip = concatenate_videoclips([clip_a, clip_b_final])
                except Exception as e:
                    print(f"⚠️ Digital Zoom Failed: {e}")
                    if logger:
                        logger.error(f"Digital Zoom Error: {e}")

            # 3.5 Apply Resolution Scaling (only for solo mode really)
            if output_resolution != "source":
                try:
                    out_w, out_h = map(int, output_resolution.split("x"))
                    cropped_clip = cropped_clip.with_effects(
                        [Resize(width=out_w, height=out_h)]
                    )
                    msg = f"📐 Scaled to {out_w}x{out_h}"
                    print(msg)
                    if logger:
                        logger.log(msg, "INFO")
                except Exception as e:
                    msg = f"⚠️ Resolution scaling failed: {e} — using source size"
                    print(msg)
                    if logger:
                        logger.error(msg)

        # 3.6 Background Music
        try:
            music_dir = os.path.join(os.getcwd(), "assets", "music")
            music_files = (
                [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
                if os.path.exists(music_dir)
                else []
            )

            if music_files:
                import random

                bg_music_path = os.path.join(music_dir, random.choice(music_files))

                # Load Music
                bg_music = AudioFileClip(bg_music_path)

                # Loop if needed
                if bg_music.duration < duration:
                    bg_music = bg_music.loop(duration=duration)
                else:
                    bg_music = bg_music.subclipped(0, duration)

                # Set Volume (Ducking - simple constant low volume)
                # -20dB is approx 0.1
                bg_music = bg_music.with_volume_scaled(0.10)

                # Composite
                original_audio = cropped_clip.audio
                final_audio = CompositeAudioClip([original_audio, bg_music])
                cropped_clip.audio = final_audio

                msg = f"🎵 Added Background Music: {os.path.basename(bg_music_path)}"
                print(msg)
                if logger:
                    logger.log(msg, "INFO", "PURPLE")
        except Exception as e:
            pass

        # --- PHASE 8: AUDIO POLISH (De-Clicking) ---
        # Apply ultra-short fade in/out to prevent pops
        if cropped_clip.audio:
            cropped_clip = cropped_clip.with_effects(
                [
                    # MoviePy 2.x audio effects are applied via with_effects or directly on audio?
                    # Actually audio_fadein is a method of AudioFileClip, but often exposed on VideoClip in v1.
                    # In v2, it's safer to operate on .audio
                    # BUT, .audio_fadein returning a new clip is standard.
                    # Let's try the standard v1/v2 compatible way if available, else .audio.
                ]
            )
            # Manual fade on audio track
            try:
                new_audio = cropped_clip.audio.with_effects(
                    [AudioFadeIn(0.05), AudioFadeOut(0.05)]
                )
                cropped_clip.audio = new_audio
            except Exception as e:
                # Fallback or ignore if fails (not critical)
                pass

        # 4. Generate ASS Subtitles

        generator = SubtitleGenerator(
            style_name=style_name,
            font_size=int(font_size),
            position=position,
            custom_config=custom_config,  # NEW
        )

        # Adjust timestamp relative to clip start
        words_relative = []
        for w in clip_data.get("words", []):
            words_relative.append(
                {
                    "word": w["word"],
                    "start": w["start"] - start_t,
                    "end": w["end"] - start_t,
                }
            )

        ass_path = os.path.join(
            self.temp_dir, f"captions_{os.path.basename(output_path)}.ass"
        )
        # Ensure path uses forward slashes for FFmpeg compatibility
        ass_path = ass_path.replace("\\", "/")

        generator.generate_ass_file(words_relative, ass_path)

        # 5. Render with NVENC + Subtitles Filter
        temp_audio = os.path.join(self.temp_dir, "temp-audio.m4a")

        try:
            msg = "🚀 Rendering with NVIDIA NVENC (RTX 4060) + ASS Captions..."
            print(msg)
            if logger:
                logger.log(msg, "INFO")

            # Escape colons in path for ffmpeg filter (e: -> e\:)
            # Actually, standard forward slashes usually work if quoted.
            # Best safe way for subtitles filter on Windows:
            # subtitles='E\:/path/to/file.ass'

            # Simple replace for drive letter colon
            safe_ass_path = ass_path.replace(":", "\\:")

            # --- Quality Params (Premiere Pro YouTube Export Match) ---
            extra_params = []
            if output_bitrate == "auto":
                # VBR targeting 26 Mbps (Premiere Pro "Match Source - High Bitrate")
                extra_params.extend(
                    [
                        "-b:v",
                        "26M",
                        "-maxrate",
                        "30M",
                        "-bufsize",
                        "52M",
                    ]
                )
            else:
                extra_params.extend(
                    [
                        "-b:v",
                        output_bitrate,
                        "-maxrate",
                        output_bitrate,
                        "-bufsize",
                        output_bitrate,
                    ]
                )

            # FULL FFmpeg Params — Premiere Pro compatible
            ffmpeg_params = [
                "-preset",
                "p4",
                "-profile:v",
                "high",
                "-level:v",
                "4.2",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                f"subtitles='{safe_ass_path}'",
            ] + extra_params

            cropped_clip.write_videofile(
                output_path,
                codec="h264_nvenc",
                audio_codec="aac",
                audio_bitrate="320k",
                temp_audiofile=temp_audio,
                remove_temp=True,
                ffmpeg_params=ffmpeg_params,
                threads=8,
                fps=fps,
                logger=proglog_logger,
            )

            msg = f"✅ NVENC Success: {output_path}"
            print(msg)
            if logger:
                logger.log(msg, "INFO", "GREEN")

            # Generate Thumbnail
            thumbnail_path = output_path.replace(".mp4", ".jpg")
            try:
                # Save frame from middle of clip
                cropped_clip.save_frame(thumbnail_path, t=duration / 2)
                if logger:
                    logger.log(f"🖼️ Thumbnail generated: {thumbnail_path}", "INFO")
            except Exception as e:
                print(f"⚠️ Thumbnail generation failed: {e}")
                thumbnail_path = ""

            return output_path, thumbnail_path

        except Exception as e:
            msg = f"⚠️ NVENC Failed. Falling back to CPU... Error: {e}"
            print(msg)
            if logger:
                logger.error(msg)

            # Fallback CPU Rendering (still high quality)
            cropped_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                audio_bitrate="320k",
                temp_audiofile=temp_audio,
                remove_temp=True,
                preset="slow",
                ffmpeg_params=[
                    "-profile:v",
                    "high",
                    "-level:v",
                    "4.2",
                    "-pix_fmt",
                    "yuv420p",
                    "-crf",
                    "18",
                    "-vf",
                    f"subtitles='{safe_ass_path}'",
                ],
                fps=fps,
                logger=proglog_logger,
            )

        # Cleanup
        original_clip.close()
        cropped_clip.close()
        if os.path.exists(ass_path):
            os.remove(ass_path)


if __name__ == "__main__":
    print("Test mode: Please run via launch.bat")
