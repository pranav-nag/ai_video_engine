import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
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
    ):
        """
        Renders a single viral clip with:
        1. 9:16 Crop (Dynamic Center)
        2. ASS Subtitles (Karaoke + Pop)
        3. NVENC Acceleration (RTX 4060)
        4. B-Roll Overlay (when no face detected)
        """
        msg = f"🎬 Initializing Render: {output_path} | Style: {style_name} | Font Size: {font_size}px"
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

            # 3. Fetch B-Roll for intervals
            if b_roll_intervals:
                manager = BRollManager()
                if manager.b_roll_files:
                    msg = f"🎥 Found {len(b_roll_intervals)} 'No Face' segments. Inserting B-Roll..."
                    print(msg)
                    if logger:
                        logger.log(msg, "INFO", "CYAN")

                    for b_start, b_end in b_roll_intervals:
                        b_dur = b_end - b_start
                        b_clip = manager.get_random_b_roll(b_dur)
                        if b_clip:
                            b_roll_clips.append(
                                {"start": b_start, "end": b_end, "clip": b_clip}
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

        def _interpolate_crop_x(t):
            """Find the best crop_x for absolute time t using crop_map."""
            frame_idx = int(t * fps)
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
            val = crop_map[k_before] + ratio * (crop_map[k_after] - crop_map[k_before])
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

        # 3.5 Apply Resolution Scaling (if requested)
        if output_resolution != "source":
            try:
                out_w, out_h = map(int, output_resolution.split("x"))
                cropped_clip = cropped_clip.resized((out_w, out_h))
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
            print(f"⚠️ Music Integration Failed: {e}")

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
