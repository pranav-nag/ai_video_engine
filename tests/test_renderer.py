import sys
import os
from unittest.mock import MagicMock

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.renderer import VideoRenderer


def test_renderer_args():
    print("Testing VideoRenderer signature...")
    renderer = VideoRenderer()

    # Mocking to avoid actual rendering which is slow and needs files
    # We just want to check if arguments are accepted without TypeError
    try:
        # Create dummy arguments
        video_path = "dummy.mp4"
        clip_data = {"start": 0, "end": 10, "words": []}
        crop_map = {}
        output_path = "output.mp4"

        # We expect this to fail on file IO, but NOT on argument mismatch
        try:
            renderer.render_clip(
                video_path,
                clip_data,
                crop_map,
                output_path,
                style_name="Hormozi",
                font_size=80,
                position="top",
            )
        except OSError:
            # Expected because file doesn't exist
            print("✅ Arguments accepted (OSError on missing file is expected)")
        except TypeError as e:
            print(f"❌ TypeError: {e}")
            return

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    test_renderer_args()
