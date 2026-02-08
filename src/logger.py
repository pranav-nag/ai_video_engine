import logging
import os
import re
from datetime import datetime


class VideoLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger = None
        self.current_log_file = None
        self.ui_callback = None

    def setup(self, video_title, ui_callback=None):
        """
        Sets up a new logger for a specific video processing session.
        """
        # Sanitize title for filename
        safe_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
        safe_title = safe_title.replace(" ", "_")[:50]  # Limit length
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.log"
        self.current_log_file = os.path.join(self.log_dir, filename)

        # Configure logging
        self.logger = logging.getLogger(f"VideoLogger_{timestamp}")
        self.logger.setLevel(logging.INFO)

        # File Handler
        fh = logging.FileHandler(self.current_log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(fh)

        # Store UI callback for real-time updates
        self.ui_callback = ui_callback

        self.info(f"📝 Log file created: {self.current_log_file}")
        return self.current_log_file

    def log(self, message, level="INFO", color=None):
        """Unified logging to file and UI."""
        if not self.logger:
            print(f"[NO_LOGGER] {message}")
            return

        # File Log
        if level == "INFO":
            self.logger.info(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)

        # UI Log (if callback provided)
        if self.ui_callback:
            self.ui_callback(message, color=color)

    def rename_log_file(self, new_title):
        """Renames the current log file to include the video title."""
        if not self.current_log_file or not os.path.exists(self.current_log_file):
            return

        self.close()  # Close handlers first

        try:
            # Generate new filename
            safe_title = re.sub(r'[\\/*?:"<>|]', "", new_title)
            safe_title = safe_title.replace(" ", "_")[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{safe_title}_{timestamp}.log"
            new_path = os.path.join(self.log_dir, new_filename)

            os.rename(self.current_log_file, new_path)
            self.current_log_file = new_path

            # Re-initialize logger with new file
            self.logger = logging.getLogger(f"VideoLogger_{timestamp}")
            self.logger.setLevel(logging.INFO)
            fh = logging.FileHandler(self.current_log_file, encoding="utf-8")
            fh.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(fh)

            self.info(f"🔄 Log file renamed to: {new_filename}")
        except Exception as e:
            print(f"Failed to rename log file: {e}")

    def info(self, message, color=None):
        self.log(message, "INFO", color)

    def error(self, message, color=None):
        import traceback

        self.log(f"{message}\n{traceback.format_exc()}", "ERROR", color)

    def warning(self, message, color=None):
        self.log(message, "WARNING", color)

    def capture_ollama_logs(self):
        """Attempts to read local Ollama logs and append them to the current log."""
        # Standard path for Ollama logs on Windows
        ollama_log_path = os.path.expandvars(r"%LOCALAPPDATA%\Ollama\server.log")

        if not os.path.exists(ollama_log_path):
            self.log(
                "⚠️ Ollama log file not found at default location.", level="WARNING"
            )
            return

        try:
            self.log("🔍 Scraping Ollama Server Logs for context...", color=None)
            with open(ollama_log_path, "r", encoding="utf-8", errors="ignore") as f:
                # Read the last 50 lines to catch recent activity
                lines = f.readlines()
                recent_logs = lines[-50:]

                if self.logger:
                    self.logger.info("=== OLLAMA SERVER INTERNAL LOGS ===")
                    for line in recent_logs:
                        self.logger.info(f"[Ollama] {line.strip()}")
                    self.logger.info("====================================")

            # Also check for common error patterns in the last logs
            combined_logs = "".join(recent_logs)
            if "failure during GPU discovery" in combined_logs:
                self.log(
                    "🚨 Ollama reported GPU discovery issues. This might slow down processing.",
                    color="ORANGE",
                )

        except Exception as e:
            self.error(f"Failed to capture Ollama logs: {e}")

    def close(self):
        """Closes handlers to release file lock."""
        if self.logger:
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)
            self.logger = None
