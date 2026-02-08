import os
import json
import requests
import cv2
from dotenv import load_dotenv
from src.scene_detect import SceneDetector
from src.vision_analyzer import VisionAnalyzer

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# UPDATED: Upgraded to Qwen 2.5 for better video/vision analysis on 8GB VRAM
OLLAMA_MODEL = "qwen2.5:7b"
# Default to 4096, but allow lower for 8GB VRAM cards
OLLAMA_CTXLEN = int(os.getenv("OLLAMA_CTXLEN", "4096"))
CHUNK_SIZE = 4000


def ensure_ollama_running():
    """Checks if Ollama is running and verifies model availability."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"✅ Ollama is running. Available: {models}")

            if OLLAMA_MODEL not in models:
                print(f"⚠️  WARNING: Model '{OLLAMA_MODEL}' not found in Ollama!")
                print(f"👉 Fix: Run 'ollama pull {OLLAMA_MODEL}' in terminal.")
                return False
            return True
    except Exception:
        print("❌ Ollama is NOT running. Please start it.")
        return False


def format_transcript_with_time(word_list):
    """
    Converts word list to time-coded string, grouped by 5-second chunks
    to reduce token noise and help Llama see 'sentences'.
    """
    formatted_text = ""
    current_time_bucket = -1

    for w in word_list:
        start_time = int(w["start"])
        # Bucket every 5 seconds (0, 5, 10...)
        bucket = (start_time // 5) * 5

        if bucket > current_time_bucket:
            formatted_text += f"\n[{bucket}s] "
            current_time_bucket = bucket
        formatted_text += f"{w['word']} "

    return formatted_text


def snap_to_scenes(clip_start, clip_end, scenes, max_shift=3.0):
    """
    Snap clip boundaries to nearest scene boundaries for professional cuts.

    Args:
        clip_start: AI-suggested clip start time (seconds)
        clip_end: AI-suggested clip end time (seconds)
        scenes: List of scene dicts with 'start' and 'end' keys
        max_shift: Maximum seconds we'll adjust boundaries (default 3s)

    Returns:
        Tuple of (snapped_start, snapped_end)
    """
    if not scenes:
        return clip_start, clip_end

    best_start = clip_start
    best_end = clip_end

    # Find nearest scene start within max_shift
    for scene in scenes:
        if abs(scene["start"] - clip_start) < max_shift:
            if abs(scene["start"] - clip_start) < abs(best_start - clip_start):
                best_start = scene["start"]

    # Find nearest scene end within max_shift
    for scene in scenes:
        if abs(scene["end"] - clip_end) < max_shift:
            if abs(scene["end"] - clip_end) < abs(best_end - clip_end):
                best_end = scene["end"]

    return best_start, best_end


def analyze_transcript(
    transcript_text, min_sec=15, max_sec=60, logger=None, video_path=None
):
    """
    Sends transcript to Ollama.
    Now optionally uses visual SCENE BOUNDARIES to guide the AI.
    """
    if not ensure_ollama_running():
        return []

    # --- Log System Resources ---
    import psutil

    mem = psutil.virtual_memory()
    msg = f"📊 System RAM: {mem.percent}% used | Available: {mem.available / (1024**3):.1f} GB"
    print(msg)
    if logger:
        logger.log(msg, "INFO", "GREY")
        logger.log(f"🧠 Ollama Context Window: {OLLAMA_CTXLEN} tokens", "INFO", "GREY")

    # --- SCENE DETECTION (Enhanced Accuracy) ---
    # OPTIMIZATION: Detect scenes ONCE and cache for reuse (LLM context + snapping)
    scenes = []
    scene_context = ""
    if video_path and os.path.exists(video_path):
        try:
            detector = SceneDetector(threshold=27.0)
            scenes = detector.detect_scenes(video_path, logger)
            # Format scenes for LLM: "Scene 1: 0s-4s, Scene 2: 4s-12s..."
            scene_str_list = [
                f"Scene {i + 1}: {s['start']:.1f}s-{s['end']:.1f}s"
                for i, s in enumerate(scenes[:50])
            ]  # Limit to 50 scenes to save tokens
            scene_context = (
                "\nVISUAL SCENES (Use these natural cut points to avoid mid-shot cuts):\n"
                + ", ".join(scene_str_list)
            )
        except Exception as e:
            msg = f"⚠️ Scene detection failed: {e}. Falling back to text-only."
            print(msg)
            if logger:
                logger.log(msg, "WARNING")
            scenes = []  # Fallback to empty list

    # OPTIMIZATION: Free memory after scene detection
    import gc

    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except:
        pass  # Torch may not be imported yet

    # --- NEW: Chunking Logic for Long Videos ---
    # Max words per AI request (approx 8-10 mins of speech)
    MAX_WORDS_PER_CHUNK = 1500
    words = transcript_text.split()

    # If transcript is long, we disable scene context for chunks to simplify (or we could split scenes too, but let's keep it simple for now)
    if len(words) > MAX_WORDS_PER_CHUNK:
        msg = f"📦 Transcript is long ({len(words)} words). Processing in chunks..."
        print(msg)
        if logger:
            logger.log(msg, "INFO")

        all_clips = []

        # Process in chunks with 10% overlap (to catch clips on boundaries)
        step = int(MAX_WORDS_PER_CHUNK * 0.9)
        for i in range(0, len(words), step):
            chunk_text = " ".join(words[i : i + MAX_WORDS_PER_CHUNK])
            msg = f"🎬 Analyzing Chunk {i // step + 1}..."
            print(msg)
            if logger:
                logger.log(msg, "INFO")

            chunk_clips = analyze_transcript(
                chunk_text, min_sec, max_sec, logger, video_path=None
            )
            all_clips.extend(chunk_clips)

        # Deduplicate and Sort
        unique_clips = []
        seen_starts = set()
        for c in all_clips:
            if c["start"] not in seen_starts:
                unique_clips.append(c)
                seen_starts.add(c["start"])

        unique_clips.sort(key=lambda x: x["score"], reverse=True)
        return unique_clips[:10]  # Return top 10 from long video

    # --- Existing Single-Chunk Logic ---

    system_prompt = (
        "You are an expert Video Editor for viral TikToks and Shorts. "
        "Your goal is to find the MOST engaging, standalone segments from the transcript. "
        "You have access to the transcript and (optionally) visual scene boundaries. "
        "RULES:\n"
        f"1. EXTREMELY IMPORTANT: Each clip MUST be between {min_sec} and {max_sec} seconds long. "
        f"2. DO NOT output clips shorter than {min_sec} seconds. "
        "3. CRITICAL: Clips MUST start and end at Scene Boundaries when provided. "
        "   Choose the CLOSEST scene boundary to your desired moment. "
        "   Example: If you want 10s-25s but Scene 2 is 9s-26s, use 9s-26s. "
        "   This ensures smooth, professional cuts without jarring mid-action transitions. "
        "4. SCORE CRITERIA (0-100): "
        "   - 90-100: High Energy, Emotional Peak, Controversial Statement, or 'Wait for it' moment. "
        "   - 70-89: Solves a problem, tells a complete story, or is funny. "
        "   - 60-69: Good content, but maybe less 'viral' - STILL INCLUDE if coherent. "
        "   - < 60: Boring, Ignore. "
        "5. SMART DURATION: "
        "   - If the moment is a quick punchline or shock, keep it SHORT (15-30s). "
        "   - If it's a story or explanation, allow it to be LONGER (45-60s). "
        "6. Return ONLY valid JSON. "
        'Format: {"clips": [{"start": float, "end": float, "score": int, "hook": "string", "reason": "string", "duration_type": "short_burst" | "story_mode"}]}'
    )

    # Payload for /api/chat
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Analyze this transcript and find 3-5 viral clips ({min_sec}-{max_sec}s).\n{scene_context}\nTRANSCRIPT:\n{transcript_text}",
            },
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.7,  # Slightly creative but focused
            "num_ctx": OLLAMA_CTXLEN,  # Ensure enough context for long videos
        },
    }

    try:
        msg = f"🧠 AI is analyzing for viral clips (using {OLLAMA_MODEL})..."
        print(msg)
        if logger:
            logger.log(msg, "INFO", "PURPLE")

        # Add timeout (300s = 5 mins) to prevent infinite hangs
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=300)
        response.raise_for_status()

        result = response.json()
        response_text = result.get("message", {}).get("content", "")

        try:
            # 1. First, try simple decode
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # 2. Robust Regex Extraction for Multiple JSON Objects

            # Find all JSON-like structures (objects)
            # This regex looks for { ... } non-greedily, but we need to arguably be careful with nesting.
            # A better approach for LLM "concatenated JSON" is to just find all top-level {} blocks.

            extracted_clips = []

            # Basic attempt to find code blocks first
            clean_text = response_text
            if "```json" in response_text:
                clean_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                clean_text = response_text.split("```")[1].split("```")[0].strip()

            # Regex to find balanced top-level braces is hard, so let's use a decoder approach
            # We will try to parse continuously from the string.
            decoder = json.JSONDecoder()
            pos = 0
            while pos < len(clean_text):
                # Skip whitespace
                while pos < len(clean_text) and clean_text[pos].isspace():
                    pos += 1
                if pos >= len(clean_text):
                    break

                # Check if we are at a start of an object
                if clean_text[pos] != "{":
                    # Skip until next '{'
                    pos += 1
                    continue

                try:
                    obj, end_pos = decoder.raw_decode(clean_text, idx=pos)
                    pos = end_pos

                    # Consolidate results
                    if isinstance(obj, dict):
                        if "clips" in obj:
                            extracted_clips.extend(obj["clips"])
                        else:
                            # Maybe the object itself is a clip? (Unlikely given prompt, but possible)
                            if "start" in obj and "end" in obj:
                                extracted_clips.append(obj)
                    elif isinstance(obj, list):
                        extracted_clips.extend(obj)

                except json.JSONDecodeError:
                    pos += 1  # Move forward and try again

            if extracted_clips:
                data = {"clips": extracted_clips}
            else:
                # 3. Fallback: Last ditch brute force for a single object if the above failed completely
                try:
                    start_idx = response_text.find("{")
                    end_idx = response_text.rfind("}")
                    if start_idx != -1 and end_idx != -1:
                        json_str = response_text[start_idx : end_idx + 1]
                        data = json.loads(json_str)
                    else:
                        raise ValueError("No JSON found")
                except Exception:
                    print("❌ JSON Parsing Failed.")
                    if "response_text" in locals():
                        print(f"📄 Raw Output (snippet): {response_text[:500]}...")
                    return []

        # Standardize Data Structure
        if isinstance(data, list):
            raw_clips = data
        else:
            raw_clips = data.get("clips", [])

        # CLEANING & VALIDATION
        clips = []
        for x in raw_clips:
            # Ensure start/end/score are not None
            start = x.get("start")
            end = x.get("end")
            score = x.get("score")

            # Helper to safely convert numbers
            def safe_float(v):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None

            s_val = safe_float(start)
            e_val = safe_float(end)

            if s_val is not None and e_val is not None:
                # [NEW] Duration Validation - Use user's min_sec parameter
                duration = e_val - s_val
                if duration < min_sec:
                    print(
                        f"⚠️ Skipping short clip ({duration:.1f}s < {min_sec}s): {x.get('hook', 'Unknown')}"
                    )
                    continue

                # [SCENE-AWARE] Snap to nearest scene boundaries (if available)
                # OPTIMIZATION: Reuse cached scenes from earlier detection (line 119)
                if scenes:  # If we have cached scene data
                    try:
                        s_val, e_val = snap_to_scenes(
                            s_val, e_val, scenes, max_shift=3.0
                        )

                        # Re-validate duration after snapping
                        duration = e_val - s_val
                        if duration < min_sec or duration > max_sec:
                            print(
                                f"⚠️ Skipping clip after scene-snap ({duration:.1f}s out of range): {x.get('hook', 'Unknown')}"
                            )
                            continue
                    except:
                        pass  # Fall back to original timestamps if snapping fails

                # Force to float/int
                try:
                    cleaned_clip = {
                        "start": s_val,
                        "end": e_val,
                        "score": int(score) if safe_float(score) is not None else 0,
                        "hook": str(x.get("hook", "No Hook")),
                        "reason": str(x.get("reason", "No reason provided")),
                        "duration_type": str(x.get("duration_type", "unknown")),
                    }
                    clips.append(cleaned_clip)
                except (ValueError, TypeError):
                    continue

        # Sort by score (Robustly)
        clips.sort(key=lambda x: x["score"], reverse=True)

        # Sort by score (Robustly)
        clips.sort(key=lambda x: x["score"], reverse=True)
        top_clips = clips[:5]

        # --- VISION ANALYSIS (Hybrid Scoring) ---
        if video_path and os.path.exists(video_path):
            try:
                msg = f"👁️ Analying Visuals for Top {len(top_clips)} Clips..."
                print(msg)
                if logger:
                    logger.log(msg, "INFO", "PURPLE")

                vision = VisionAnalyzer()
                # We only analyze the specific time ranges of the top clips to save time/compute
                for clip in top_clips:
                    # Extract middle frame of the clip for scoring
                    mid_point = (clip["start"] + clip["end"]) / 2

                    # Quick frame extraction using CV2 (we could add a method to VisionAnalyzer for this)
                    cap = cv2.VideoCapture(video_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, mid_point * 1000)
                    ret, frame = cap.read()
                    cap.release()

                    if ret:
                        temp_frame = f"temp_frame_{mid_point}.jpg"
                        cv2.imwrite(temp_frame, frame)

                        prompt = 'Rate this video frame for viral potential (0-100). Is it visually interesting? JSON: {"score": int}'
                        # Simple synchronous call
                        response_text = vision.analyze_frame(temp_frame, prompt)

                        if os.path.exists(temp_frame):
                            os.remove(temp_frame)

                        # Parse visual score
                        visual_score = 0
                        try:
                            # Basic cleanup
                            clean = (
                                response_text.replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )
                            v_data = json.loads(clean)
                            visual_score = int(v_data.get("score", 0))
                        except:
                            pass

                        # Weighted Score: 70% Text, 30% Visual
                        old_score = clip["score"]
                        new_score = int((old_score * 0.7) + (visual_score * 0.3))
                        clip["score"] = new_score
                        clip["reason"] += f" | Visual: {visual_score}/100"

                        if logger:
                            logger.log(
                                f"   Clip '{clip['hook'][:15]}...': Text={old_score}, Vis={visual_score} -> Final={new_score}",
                                "INFO",
                            )

            except Exception as e:
                if logger:
                    logger.log(f"⚠️ Vision analysis skipped: {e}", "WARNING")

        # Re-sort after visual scoring
        top_clips = clips[:5]

        # --- VISION ANALYSIS (Hybrid Scoring) ---
        if video_path and os.path.exists(video_path):
            try:
                msg = f"👁️ Analyzing Visuals for Top {len(top_clips)} Clips..."
                print(msg)
                if logger:
                    logger.log(msg, "INFO", "PURPLE")

                vision = VisionAnalyzer()
                # We only analyze the specific time ranges of the top clips to save time/compute
                for clip in top_clips:
                    # Extract middle frame of the clip for scoring
                    mid_point = (clip["start"] + clip["end"]) / 2

                    # Quick frame extraction using CV2
                    cap = cv2.VideoCapture(video_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, mid_point * 1000)
                    ret, frame = cap.read()
                    cap.release()

                    if ret:
                        temp_frame = f"temp_frame_{mid_point}.jpg"
                        cv2.imwrite(temp_frame, frame)

                        prompt = 'Rate this video frame for viral potential (0-100). Is it visually interesting? JSON: {"score": int}'
                        # Simple synchronous call
                        response_text = vision.analyze_frame(temp_frame, prompt)

                        if os.path.exists(temp_frame):
                            os.remove(temp_frame)

                        # Parse visual score
                        visual_score = 0
                        try:
                            # Basic cleanup
                            clean = (
                                response_text.replace("```json", "")
                                .replace("```", "")
                                .strip()
                            )
                            if "{" in clean:
                                import json as j

                                v_data = j.loads(clean)
                                visual_score = int(v_data.get("score", 0))
                        except Exception:
                            pass

                        # Weighted Score: 70% Text, 30% Visual
                        old_score = clip["score"]
                        new_score = int((old_score * 0.7) + (visual_score * 0.3))
                        clip["score"] = new_score
                        clip["reason"] += f" | Visual: {visual_score}/100"

                        if logger:
                            logger.log(
                                f"   Clip '{clip['hook'][:15]}...': Text={old_score}, Vis={visual_score} -> Final={new_score}",
                                "INFO",
                            )

            except Exception as e:
                # Log but do not fail
                if logger:
                    logger.log(f"⚠️ Vision analysis skipped: {e}", "WARNING")

        # Final Sort
        top_clips.sort(key=lambda x: x["score"], reverse=True)

        msg = f"🔥 AI successfully found {len(top_clips)} viral clips."
        print(msg)
        if logger:
            logger.log(msg, "INFO", "GREEN")
        return top_clips

    except Exception as e:
        msg = f"❌ Analysis Error: {e}"
        print(msg)
        if logger:
            logger.error(msg)
        # If possible, show what failed
        if "response_text" in locals() and response_text:
            print(f"📄 Raw Output was: {response_text[:200]}...")
        return []


if __name__ == "__main__":
    # Test block
    mock_text = (
        "[0.0s] This is a test [5.0s] for a viral video [10.0s] that we are making."
    )
    print(analyze_transcript(mock_text))
