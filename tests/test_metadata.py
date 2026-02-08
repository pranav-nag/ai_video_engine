import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest_transcribe import VideoIngestor


def test_metadata():
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo (short)
    print(f"Testing metadata fetch for: {url}")

    ingestor = VideoIngestor()
    duration, title = ingestor.get_video_info(url)

    print(f"Duration: {duration}")
    print(f"Title: {title}")

    if duration > 0 and title:
        print("✅ Metadata fetch successful!")
    else:
        print("❌ Metadata fetch failed.")


if __name__ == "__main__":
    test_metadata()
