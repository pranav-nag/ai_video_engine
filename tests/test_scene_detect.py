import sys
import os

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scene_detect import SceneDetector


def test_scene_detector():
    print("Testing SceneDetector Import...")
    try:
        SceneDetector()
        print("✅ SceneDetector initialized.")

        # Check if library is available
        from src.scene_detect import SCENEDETECT_AVAILABLE

        if SCENEDETECT_AVAILABLE:
            print("✅ PySceneDetect library is AVAILABLE and loaded.")
        else:
            print(
                "❌ PySceneDetect library is MISSING (This should not happen if you installed specific-requirements)."
            )

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_scene_detector()
