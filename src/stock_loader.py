import os
import requests
import random
import time
from dotenv import load_dotenv

load_dotenv()


class StockDownloader:
    """
    Downloads stock footage for B-Roll.
    Priority:
    1. Pexels API (if PEXELS_API_KEY is found)
    2. Fallback Hardcoded Public Domain URLs (if API fails or missing)
    """

    def __init__(self, asset_dir=r"assets/b_roll"):
        self.asset_dir = asset_dir
        if not os.path.exists(self.asset_dir):
            os.makedirs(self.asset_dir)

        self.pexels_key = os.getenv("PEXELS_API_KEY")

        # fallback generic vertical videos (Creative Commons / Public Domain)
        # using placeholder Pexels video links that are public
        self.FALLBACK_VIDEOS = {
            "money": [
                "https://videos.pexels.com/video-files/7565438/7565438-hd_1080_1920_30fps.mp4",  # Falling money
                "https://videos.pexels.com/video-files/4990232/4990232-hd_1080_1920_30fps.mp4",  # Counting money
            ],
            "tech": [
                "https://videos.pexels.com/video-files/5473806/5473806-hd_1080_1920_30fps.mp4",  # Coding matrix
                "https://videos.pexels.com/video-files/3129671/3129671-hd_1080_1920_30fps.mp4",  # HUD
            ],
            "nature": [
                "https://videos.pexels.com/video-files/855018/855018-hd_1080_1920_30fps.mp4",  # Forest
            ],
            "city": [
                "https://videos.pexels.com/video-files/3753696/3753696-hd_1080_1920_30fps.mp4",  # Traffic
            ],
            "generic": [
                "https://videos.pexels.com/video-files/855018/855018-hd_1080_1920_30fps.mp4",  # Clouds/Nature
            ],
        }

    def download_stock(self, keyword, logger=None):
        """
        Attempts to download a video for the keyword.
        Returns the path to the downloaded file, or None.
        """
        # Sanitization
        keyword = keyword.lower().strip()
        filename = f"{keyword}_{int(time.time())}.mp4"
        output_path = os.path.join(self.asset_dir, filename)

        # 1. Try Pexels API
        if self.pexels_key:
            if logger:
                logger.log(f"🌍 Searching Pexels for '{keyword}'...", "INFO")
            try:
                # Pexels Video Search API
                url = "https://api.pexels.com/videos/search"
                headers = {"Authorization": self.pexels_key}
                params = {
                    "query": keyword,
                    "per_page": 3,
                    "orientation": "portrait",  # 9:16 preference
                    "size": "medium",  # 1080p usually
                }

                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("videos"):
                    # Pick random video
                    vid = random.choice(data["videos"])
                    # Get best quality file (closest to 1080w or 1080h)
                    # Pexels files structure: list of 'video_files' dicts
                    video_files = vid.get("video_files", [])
                    # Filter for HD
                    hd_files = [
                        v
                        for v in video_files
                        if v["height"] >= 1280 or v["width"] >= 720
                    ]
                    if not hd_files:
                        hd_files = video_files

                    target_file = hd_files[0]
                    download_url = target_file["link"]

                    self._download_url(download_url, output_path, logger)
                    return output_path
                else:
                    if logger:
                        logger.log(
                            f"⚠️ No Pexels results for '{keyword}'. Using fallback.",
                            "WARNING",
                        )

            except Exception as e:
                if logger:
                    logger.log(f"⚠️ Pexels API Error: {e}", "WARNING")

        # 2. Fallback
        return self._download_fallback(keyword, output_path, logger)

    def _download_fallback(self, keyword, output_path, logger=None):
        """Matches keyword to basic category categories."""
        # Simple mapping
        category = "generic"
        if any(k in keyword for k in ["money", "cash", "rich", "dollar", "profit"]):
            category = "money"
        elif any(k in keyword for k in ["tech", "ai", "robot", "code", "future"]):
            category = "tech"
        elif any(k in keyword for k in ["tree", "world", "earth"]):
            category = "nature"
        elif any(k in keyword for k in ["city", "traffic", "busy"]):
            category = "city"

        url_list = self.FALLBACK_VIDEOS.get(category, self.FALLBACK_VIDEOS["generic"])
        url = random.choice(url_list)

        if logger:
            logger.log(
                f"📥 Downloading fallback stock ({category}) for '{keyword}'...",
                "INFO",
                "CYAN",
            )
        return self._download_url(url, output_path, logger)

    def _download_url(self, url, output_path, logger):
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            if logger:
                logger.log(
                    f"✅ Saved B-Roll: {os.path.basename(output_path)}", "INFO", "GREEN"
                )
            return output_path
        except Exception as e:
            if logger:
                logger.error(f"Download Failed: {e}")
            return None


if __name__ == "__main__":
    # Test
    # dl = StockDownloader()
    # print(dl.download_stock("coding"))
    pass
