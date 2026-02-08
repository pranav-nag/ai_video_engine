import os
import sys

# Mock environment variable for testing
os.environ["OLLAMA_CTXLEN"] = "2048"

# Add project root to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("--- Testing Analyzer Config ---")
    from src import analyzer

    print(f"OLLAMA_CTXLEN: {analyzer.OLLAMA_CTXLEN}")
    if analyzer.OLLAMA_CTXLEN == 2048:
        print("✅ analyzer.py correctly read OLLAMA_CTXLEN from env.")
    else:
        print(
            f"❌ analyzer.py failed to read OLLAMA_CTXLEN. Got: {analyzer.OLLAMA_CTXLEN}"
        )

    print("\n--- Testing Cropper suppression ---")
    # We need to check if GLOG_minloglevel is set *before* mediapipe is fully initialized
    # But since we import it, it should be set by the module level code.
    from src import cropper

    val = os.environ.get("GLOG_minloglevel")
    print(f"GLOG_minloglevel: {val}")
    if val == "2":
        print("✅ cropper.py correctly set GLOG_minloglevel.")
    else:
        print(f"❌ cropper.py failed to set GLOG_minloglevel. Got: {val}")

except Exception as e:
    print(f"❌ Test Failed with error: {e}")
