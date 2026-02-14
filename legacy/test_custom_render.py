import os
import shutil
from src.renderer import VideoRenderer


def test_custom_render():
    print("Testing Custom Render Logic...")

    # 1. Setup Dummy Data
    mock_clip = {
        "start": 0,
        "end": 5,
        "words": [
            {"word": "Hello", "start": 0.5, "end": 1.0},
            {"word": "World", "start": 1.0, "end": 1.5},
        ],
    }

    # Custom Config to Test
    custom_config = {
        "Fontname": "Verdana",
        "PrimaryColour": "&H0000FF00",  # Green
        "OutlineColour": "&H000000FF",  # Red Border
    }

    # 2. Render (Mocking video path with a small blank video if needed,
    # but simplest is to trust the ASS generation part of renderer)
    # Actually, renderer.render_clip requires a real video to open.
    # Let's just test SubtitleGenerator directly as that's the unit logic.

    from src.fast_caption import SubtitleGenerator

    gen = SubtitleGenerator(style_name="Hormozi", custom_config=custom_config)

    # Check if overrides applied
    print(f"Font: {gen.style_config['Fontname']} (Expected 'Verdana')")
    print(f"Primary: {gen.style_config['PrimaryColour']} (Expected '&H0000FF00')")

    assert gen.style_config["Fontname"] == "Verdana"
    assert gen.style_config["PrimaryColour"] == "&H0000FF00"

    print("✅ Custom Config Applied Successfully to SubtitleGenerator")


if __name__ == "__main__":
    test_custom_render()
