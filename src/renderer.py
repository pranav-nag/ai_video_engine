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
        self, video_path, clip_data, crop_map, output_path, style_name="Hormozi"
    ):
        """
        Renders a single viral clip with:
        1. 9:16 Crop (Dynamic Center)
        2. Configurable Captions (Hormozi, Minimal, Neon)
        3. NVENC Acceleration (RTX 4060)
        """
        print(f"🎬 Initializing Render: {output_path} | Style: {style_name}")

        # 1. Load Video
        try:
            original_clip = VideoFileClip(video_path)
        except Exception as e:
            print(f"❌ Error: Could not open video {video_path}: {e}")
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
        if style_name == "Minimal":
            font = "Arial"
            fontsize = 40
            color = "white"
            stroke_color = None
            stroke_width = 0
            position = ("center", clip.h * 0.8)  # Lower
        elif style_name == "Neon":
            font = "Impact"
            fontsize = 70
            color = "#00ffcc"  # Cyan
            stroke_color = "#ff00ff"  # Magenta Outline
            stroke_width = 2
            position = ("center", "center")
        else:  # Hormozi (Default)
            font = "Impact"
            fontsize = 60
            color = "yellow"
            stroke_color = "black"
            stroke_width = 3
            position = ("center", clip.h * 0.7)

        for word_info in words:
            w_start = word_info["start"] - start_t
            w_end = word_info["end"] - start_t

            if w_end < 0 or w_start > clip.duration:
                continue

            try:
                txt_clip = (
                    TextClip(
                        word_info["word"].upper(),
                        fontsize=fontsize,
                        font=font,
                        color=color,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        method="caption",
                        size=(target_w * 0.8, None),
                    )
                    .set_position(position)
                    .set_start(w_start)
                    .set_end(w_end)
                )
                text_clips.append(txt_clip)
            except Exception as e:
                print(f"⚠️ TextClip failed for word '{word_info['word']}': {e}")

        # 5. Composite
        final_clip = CompositeVideoClip([cropped_clip] + text_clips)

        # 6. Render with NVENC
        temp_audio = os.path.join(self.temp_dir, "temp-audio.m4a")

        try:
            print("🚀 Rendering with NVIDIA NVENC (RTX 4060)...")
            final_clip.write_videofile(
                output_path,
                codec="h264_nvenc",
                audio_codec="aac",
                temp_audiofile=temp_audio,
                remove_temp=True,
                ffmpeg_params=["-preset", "p4", "-cq", "24"],
                threads=8,
                fps=24,
                logger=None,
            )
            print(f"✅ NVENC Success: {output_path}")
        except Exception as e:
            print(f"⚠️ NVENC Failed. Falling back to CPU... Error: {e}")
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=temp_audio,
                remove_temp=True,
                preset="ultrafast",
                fps=24,
            )

        original_clip.close()
        final_clip.close()


if __name__ == "__main__":
    print("Test mode: Please run via launch.bat")
