import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from dotenv import load_dotenv
from src.fast_caption import SubtitleGenerator

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
        style_name="Hormozi",
        font_size=60,
        position="center",
        output_bitrate="auto",
        output_resolution="1080x1920",
        logger=None,
        proglog_logger=None,
    ):
        """
        Renders a single viral clip with:
        1. 9:16 Crop (Dynamic Center)
        2. ASS Subtitles (Karaoke + Pop)
        3. NVENC Acceleration (RTX 4060)
        """
        msg = f"🎬 Initializing Render: {output_path} | Style: {style_name}"
        print(msg)
        if logger:
            logger.log(msg, "INFO")

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

        # Buffer to avoid audio glitches at boundaries
        clip = original_clip.subclipped(
            max(0, start_t), min(original_clip.duration, end_t)
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
            """Per-frame crop that follows the face."""
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

        # 4. Generate ASS Subtitles

        generator = SubtitleGenerator(
            style_name=style_name,
            font_size=int(font_size),
            position=position,
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
