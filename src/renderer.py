import os
import moviepy.config as mpc
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.all import crop  # Fixed: Direct import for the crop function
from dotenv import load_dotenv

# Load Environment Variables for Safe Paths
load_dotenv()

# --- CRITICAL: IMAGEMAGICK CONFIG ---
# This points to the folder we just cleaned up
IMAGEMAGICK_PATH = r"E:\AI_Video_Engine\assets\ImageMagick\convert.exe"

if os.path.exists(IMAGEMAGICK_PATH):
    # This tells MoviePy exactly where the exe is
    mpc.change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
    print("✅ ImageMagick linked successfully (convert.exe found).")
else:
    # Diagnostic helper
    print(f"❌ ERROR: ImageMagick NOT found at: {IMAGEMAGICK_PATH}")
    print(
        "👉 ACTION REQUIRED: Go to that folder and rename a copy of 'magick.exe' to 'convert.exe'"
    )


class VideoRenderer:
    def __init__(self):
        self.temp_dir = os.getenv("TEMP", r"E:\AI_Video_Engine\temp")
        # 'Impact' is standard on Windows. Montserrat is better if installed.
        self.font = "Impact"
        self.fontsize = 60
        self.stroke_width = 2

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
    ):
        """
        Renders a single viral clip with:
        1. 9:16 Crop (Dynamic Center)
        2. Configurable Captions (Hormozi, Minimal, Neon)
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
        clip = original_clip.subclip(
            max(0, start_t), min(original_clip.duration, end_t)
        )

        # 3. Calculate 9:16 Crop
        target_w = int(clip.h * (9 / 16))

        # Calculate average face position for this segment to avoid "jittery" movement
        segment_frames = [
            crop_map.get(int((start_t + t) * original_clip.fps), original_clip.w // 2)
            for t in range(int(end_t - start_t))
        ]

        if segment_frames:
            avg_x = sum(segment_frames) / len(segment_frames)
        else:
            avg_x = (original_clip.w - target_w) // 2

        # Fixed: Using the imported 'crop' function correctly
        cropped_clip = crop(clip, x1=int(avg_x), y1=0, width=target_w, height=clip.h)

        # 4. Generate Captions based on Style
        text_clips = []
        words = clip_data.get("words", [])

        # Style Configuration
        # Style Configuration
        if style_name == "Minimal":
            font = "Arial"
            fontsize = 40
            color = "white"
            stroke_color = "black"
            stroke_width = 1
            position_coords = ("center", clip.h * 0.8)  # Lower

        elif style_name == "Neon":
            font = "Impact"
            fontsize = 70
            color = "#00ffcc"  # Cyan
            stroke_color = "#ff00ff"  # Magenta Outline
            stroke_width = 2
            position_coords = ("center", "center")

        elif style_name == "Fire":
            font = "Impact"
            fontsize = 65
            color = "#FF4500"  # OrangeRed
            stroke_color = "#FFFF00"  # Yellow
            stroke_width = 2
            position_coords = ("center", "center")

        elif style_name == "Futuristic":
            font = "Arial"
            fontsize = 60
            color = "white"
            stroke_color = "#00BFFF"  # DeepSkyBlue
            stroke_width = 3
            position_coords = ("center", clip.h * 0.7)

        elif style_name == "Boxed":
            font = "Impact"
            fontsize = 60
            color = "white"
            stroke_color = None
            stroke_width = 0
            position_coords = ("center", clip.h * 0.75)
            # bg_color will be handled by passing it to create_styled_text

        else:  # Hormozi (Default)
            font = "Impact"
            fontsize = 60
            color = "#FFD700"  # Gold
            stroke_color = "black"
            stroke_width = 4
            position_coords = ("center", clip.h * 0.7)

        # OVERRIDE WITH USER SETTINGS
        if font_size:
            fontsize = int(font_size)

        # Map UI position strings to coordinates
        if position == "top":
            position_coords = ("center", clip.h * 0.1)
        elif position == "bottom":
            position_coords = ("center", clip.h * 0.75)
        elif position == "center":
            position_coords = ("center", "center")
        # Else keep style default if passed None/Unknown (though main_ui passes valid ones)

        # Helper for creating styled text
        def create_styled_text(
            txt,
            font,
            fsize,
            color,
            stroke_c,
            stroke_w,
            pos,
            start,
            end,
            shadow_offset=None,
            bg_color=None,
        ):
            clips_to_return = []

            # 1. Shadow Layer (Background)
            if shadow_offset and not bg_color:  # Don't do shadow if boxed
                # Calculate shadow position
                s_pos = pos
                if isinstance(pos, tuple):
                    # Try to offset the tuple elements if they are numbers
                    x, y = pos
                    off_x, off_y = shadow_offset

                    new_x = x + off_x if isinstance(x, (int, float)) else x
                    new_y = y + off_y if isinstance(y, (int, float)) else y
                    s_pos = (new_x, new_y)

                shadow_clip = (
                    TextClip(
                        txt,
                        fontsize=fsize,
                        font=font,
                        color="black",
                        method="caption",
                        size=(target_w * 0.8, None),
                    )
                    .set_position(s_pos)
                    .set_start(start)
                    .set_end(end)
                    .set_opacity(0.6)
                )
                clips_to_return.append(shadow_clip)

            # 2. Main Layer
            # Prepare args for TextClip
            kwargs = {
                "fontsize": fsize,
                "font": font,
                "color": color,
                "method": "caption",
                "size": (target_w * 0.8, None),
            }
            if stroke_c:
                kwargs["stroke_color"] = stroke_c
                kwargs["stroke_width"] = stroke_w
            if bg_color:
                kwargs["bg_color"] = bg_color

            main_clip = (
                TextClip(txt, **kwargs).set_position(pos).set_start(start).set_end(end)
            )
            clips_to_return.append(main_clip)

            return clips_to_return

        for word_info in words:
            w_start = word_info["start"] - start_t
            w_end = word_info["end"] - start_t

            if w_end < 0 or w_start > clip.duration:
                continue

            try:
                # "True Hormozi": Yellow + Black Stroke + Drop Shadow
                # "Fire": Red + Yellow Stroke + Drop Shadow

                current_shadow = None
                current_bg = None

                if style_name in ["Hormozi", "Fire"]:
                    current_shadow = (4, 4)
                elif style_name == "Boxed":
                    current_bg = "#000000"  # Black box

                generated_clips = create_styled_text(
                    word_info["word"].upper(),
                    font,
                    fontsize,
                    color,
                    stroke_color,
                    stroke_width,
                    position_coords,
                    w_start,
                    w_end,
                    shadow_offset=current_shadow,
                    bg_color=current_bg,
                )

                text_clips.extend(generated_clips)

            except Exception as e:
                print(f"⚠️ TextClip failed for word '{word_info['word']}': {e}")

        # 5. Composite
        final_clip = CompositeVideoClip([cropped_clip] + text_clips)

        # 5.5. Apply Resolution Scaling (if requested)
        if output_resolution != "source":
            try:
                target_w, target_h = map(int, output_resolution.split("x"))
                final_clip = final_clip.resize((target_w, target_h))
            except:
                pass  # If parsing fails, keep original

        # 6. Render with NVENC
        temp_audio = os.path.join(self.temp_dir, "temp-audio.m4a")

        try:
            msg = "🚀 Rendering with NVIDIA NVENC (RTX 4060)..."
            print(msg)
            if logger:
                logger.log(msg, "INFO")

            # Determine encoding params based on bitrate selection
            if output_bitrate == "auto":
                # Use CQ (Constant Quality) mode
                ffmpeg_params = ["-preset", "p4", "-cq", "24"]
            else:
                # Use VBR (Variable Bitrate) mode
                ffmpeg_params = [
                    "-preset",
                    "p4",
                    "-b:v",
                    output_bitrate,
                    "-maxrate",
                    output_bitrate,
                    "-bufsize",
                    output_bitrate,
                ]

            final_clip.write_videofile(
                output_path,
                codec="h264_nvenc",
                audio_codec="aac",
                temp_audiofile=temp_audio,
                remove_temp=True,
                ffmpeg_params=ffmpeg_params,
                threads=8,
                fps=24,
                logger=None,
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

            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=temp_audio,
                remove_temp=True,
                preset="ultrafast",
                fps=24,
                logger=None,  # MoviePy's internal logger is noisy
            )

        original_clip.close()
        final_clip.close()


if __name__ == "__main__":
    print("Test mode: Please run via launch.bat")
