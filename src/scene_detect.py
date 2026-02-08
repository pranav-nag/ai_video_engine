import os
import subprocess

try:
    from scenedetect import open_video, SceneManager
    from scenedetect.detectors import AdaptiveDetector

    SCENEDETECT_AVAILABLE = True
except ImportError:
    SCENEDETECT_AVAILABLE = False
    print("⚠️ PySceneDetect not found. Scene detection disabled.")


class SceneDetector:
    def __init__(self, threshold=27.0):
        # 27.0 is a good default for "ContentDetector".
        # Higher = fewer scenes (only big changes). Lower = more scenes.
        self.threshold = threshold

    def generate_proxy(self, video_path, logger=None):
        """Generates a fast 360p proxy for analysis."""
        try:
            proxy_path = video_path.replace(".mp4", "_proxy.mp4")
            # If a proxy already exists (maybe from previous run), use it to save time
            if os.path.exists(proxy_path):
                return proxy_path

            msg = "⚡ Generating low-res proxy for fast analysis..."
            print(msg)
            if logger:
                logger.log(msg, "INFO", "CYAN")

            # Fast 360p conversion
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                "scale=-1:360",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "28",
                "-y",
                proxy_path,
            ]

            # Run silently
            subprocess.run(
                cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return proxy_path
        except Exception as e:
            print(f"⚠️ Proxy generation failed: {e}. Using original.")
            return video_path

    def detect_scenes(self, video_path, logger=None):
        """
        Returns a list of (start_sec, end_sec) tuples.
        """
        if not SCENEDETECT_AVAILABLE:
            if logger:
                logger.log(
                    "⚠️ PySceneDetect not installed. Skipping scene detection.",
                    "WARNING",
                )
            return []

        # 1. Generate/Use Proxy for Speed
        analysis_path = self.generate_proxy(video_path, logger)

        msg = f"🎬 Detecting Scenes in {os.path.basename(analysis_path)}... (Threshold: {self.threshold})"
        print(msg)
        if logger:
            logger.log(msg, "INFO", "BLUE")

        video = open_video(analysis_path)
        scene_manager = SceneManager()

        # AdaptiveDetector is better for fast-paced videos than ContentDetector
        scene_manager.add_detector(AdaptiveDetector(adaptive_threshold=self.threshold))

        # Detect
        scene_manager.detect_scenes(video, show_progress=True)

        # Result: formatted as [(start_time, end_time), ...]
        scene_list = scene_manager.get_scene_list()

        formatted_scenes = []
        for i, scene in enumerate(scene_list):
            start = scene[0].get_seconds()
            end = scene[1].get_seconds()
            duration = end - start

            # Filter out micro-scenes (< 1s) which are usually glitches
            if duration >= 1.0:
                formatted_scenes.append(
                    {"id": i, "start": start, "end": end, "duration": duration}
                )

        # Cleanup Proxy
        if analysis_path != video_path and os.path.exists(analysis_path):
            try:
                os.remove(analysis_path)
            except:
                pass

        msg = f"✅ Found {len(formatted_scenes)} valid scenes."
        print(msg)
        if logger:
            logger.log(msg, "INFO", "GREEN")

        return formatted_scenes


if __name__ == "__main__":
    # Test
    # video = "test_video.mp4"
    # det = SceneDetector()
    # scenes = det.detect_scenes(video)
    # print(scenes)
    pass
