import sys
import os
import shutil

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.renderer import VideoRenderer


def test_styles():
    print("🎨 Testing Viral Caption Styles...")

    # Mock Data
    video_path = "tests/sample_video.mp4"  # You need a sample video here.
    # If no sample video, we create a dummy color clip using MoviePy?
    # Renderer expects input file.
    # Let's assume user has a video, or we will fail gracefully.

    if not os.path.exists(video_path):
        # Create a dummy video for testing
        print("⚠️ No sample video found. Creating dummy 'tests/sample_video.mp4'...")
        from moviepy.editor import ColorClip

        c = ColorClip(size=(1920, 1080), color=(0, 0, 255), duration=5)
        c.write_videofile(video_path, fps=24)
        print("✅ Dummy video created.")

    renderer = VideoRenderer()

    styles = ["Hormozi", "Fire", "Neon", "Minimal"]

    dummy_clip_data = {
        "start": 0,
        "end": 4,
        "words": [
            {"word": "This", "start": 0.0, "end": 0.8},
            {"word": "Is", "start": 0.8, "end": 1.6},
            {"word": "A", "start": 1.6, "end": 2.4},
            {"word": "Viral", "start": 2.4, "end": 3.2},
            {"word": "Test", "start": 3.2, "end": 4.0},
        ],
    }

    dummy_crop_map = {}  # No face tracking needed for dummy test

    for style in styles:
        output = f"tests/style_test_{style}.mp4"
        print(f"👉 Rendering {style}...")
        try:
            renderer.render_clip(
                video_path,
                dummy_clip_data,
                dummy_crop_map,
                output,
                style_name=style,
                font_size=80,
            )
            print(f"✅ Created: {output}")
        except Exception as e:
            print(f"❌ Failed {style}: {e}")


if __name__ == "__main__":
    test_styles()
