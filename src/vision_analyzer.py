import os
import base64
import cv2
import requests
from dotenv import load_dotenv

load_dotenv()


class VisionAnalyzer:
    def __init__(self, model_name="minicpm-v"):
        self.model_name = model_name
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def encode_image(self, image_path):
        """Encodes an image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_frame(
        self, frame_path, prompt="Describe this image in detail.", logger=None
    ):
        """
        Sends a single frame to the vision model.
        """
        try:
            b64_image = self.encode_image(frame_path)

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt, "images": [b64_image]}
                ],
                "stream": False,
            }

            response = requests.post(
                f"{self.ollama_url}/api/chat", json=payload, timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return result.get("message", {}).get("content", "")

        except Exception as e:
            if logger:
                logger.error(f"Vision Analysis Failed: {e}")
            return None

    def score_video_visuals(self, video_path, interval=5, logger=None):
        """
        Extracts frames every 'interval' seconds and scores them for 'Viral Potential'.
        Returns a list of {timestamp: float, visual_score: int, description: str}
        """
        if logger:
            logger.log(
                f"👁️ Analyzing visuals for {os.path.basename(video_path)}...",
                "INFO",
                "PURPLE",
            )

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        results = []

        frame_interval = int(fps * interval)
        count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if count % frame_interval == 0:
                # Save temp frame
                temp_frame = "temp_frame.jpg"
                cv2.imwrite(temp_frame, frame)

                # Analyze
                # Placeholder for actual analysis call
                # response = self.analyze_frame(temp_frame, "Analyze...", logger)

                # Clean up
                if os.path.exists(temp_frame):
                    os.remove(temp_frame)

            count += 1

        cap.release()
        return results


if __name__ == "__main__":
    # Test
    analyzer = VisionAnalyzer()
    # print(analyzer.score_video_visuals("test.mp4"))
