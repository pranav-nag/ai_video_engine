import os
import shutil
import time
from pathlib import Path


def cleanup_temp_files(temp_dir=r"E:\AI_Video_Engine\temp"):
    """
    Robustly cleans up the temporary directory.
    Retries deletion if files are locked (common with video files).
    """
    print(f"🧹 Starting cleanup of: {temp_dir}")

    if not os.path.exists(temp_dir):
        print("✅ Temp directory does not exist. Nothing to clean.")
        return

    # Helper to handle read-only files (sometimes happens with git/certain processes)
    def remove_readonly(func, path, _):
        os.chmod(path, 0o777)
        func(path)

    # Convert to Path object for easier handling
    temp_path = Path(temp_dir)

    for item in temp_path.iterdir():
        try:
            if item.is_file():
                # Try simple unlink first
                try:
                    item.unlink()
                except PermissionError:
                    # Wait a bit and try again (Windows file locking)
                    time.sleep(1.0)
                    try:
                        item.unlink()
                    except Exception:
                        print(f"⚠️ Could not delete file: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item, onerror=remove_readonly)
        except Exception as e:
            print(f"❌ Error cleaning {item.name}: {e}")

    print("✅ Cleanup sequence finished.")


if __name__ == "__main__":
    cleanup_temp_files()
