import os
import random
from moviepy.video.io.VideoFileClip import VideoFileClip
from src.stock_loader import StockDownloader


class BRollManager:
    def __init__(self, asset_dir=r"assets/b_roll"):
        self.asset_dir = asset_dir
        self.b_roll_files = []
        if os.path.exists(asset_dir):
            self.b_roll_files = [
                os.path.join(asset_dir, f)
                for f in os.listdir(asset_dir)
                if f.lower().endswith((".mp4", ".mov"))
            ]
        self.downloader = StockDownloader(asset_dir)

    def get_b_roll_for_keyword(self, keyword, duration, logger=None):
        """
        Finds or downloads B-Roll for a specific keyword.
        """
        # 1. Search Local
        matches = [
            f
            for f in self.b_roll_files
            if keyword.lower() in os.path.basename(f).lower()
        ]

        file_path = None
        if matches:
            file_path = random.choice(matches)
        else:
            # 2. auto-Download
            file_path = self.downloader.download_stock(keyword, logger=logger)
            if file_path:
                self.b_roll_files.append(file_path)  # Cache it

        if not file_path:
            return None

        return self._process_clip(file_path, duration)

    def _process_clip(self, file_path, duration, target_resolution=(1080, 1920)):
        """Helper to load and process a clip"""
        try:
            clip = VideoFileClip(file_path)
            # ... (reuse existing resizing logic) ...
            # Actually, let's just refactor get_random_b_roll to use this too
            return self._resize_and_loop(clip, duration, target_resolution)
        except Exception as e:
            print(f"⚠️ Failed to load B-Roll {file_path}: {e}")
            return None

    def _resize_and_loop(self, clip, duration, target_resolution):
        # Loop if needed
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        else:
            # Pick a random start point
            max_start = clip.duration - duration
            start = random.uniform(0, max_start)
            clip = clip.subclipped(start, start + duration)

        # Resize/Crop to 9:16 (target_resolution)
        # 1. Resize to cover (keeping aspect ratio)
        target_w, target_h = target_resolution
        clip_ratio = clip.w / clip.h
        target_ratio = target_w / target_h

        if clip_ratio > target_ratio:
            # Source is wider than target: resize by height
            new_h = target_h
            new_w = int(new_h * clip_ratio)
            clip = clip.resized(height=new_h)
            # Center crop width
            x_center = new_w / 2
            clip = clip.cropped(x1=x_center - target_w / 2, width=target_w)
        else:
            # Source is taller/narrower: resize by width
            new_w = target_w
            new_h = int(new_w / clip_ratio)
            clip = clip.resized(width=new_w)
            # Center crop height
            y_center = new_h / 2
            clip = clip.cropped(y1=y_center - target_h / 2, height=target_h)

        return clip.with_effects([])  # Ensure valid clip

    def get_random_b_roll(self, duration, target_resolution=(1080, 1920)):
        """
        Returns a VideoFileClip of the requested duration.
        """
        if not self.b_roll_files:
            return None

        # Pick random file
        file_path = random.choice(self.b_roll_files)
        return self._process_clip(file_path, duration, target_resolution)
