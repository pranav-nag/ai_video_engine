import os
import json
import requests
import cv2
import time
from dotenv import load_dotenv
from src.scene_detect import SceneDetector
from src.vision_analyzer import VisionAnalyzer

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
# UPDATED: Upgraded to Qwen 2.5 for better video/vision analysis on 8GB VRAM
OLLAMA_MODEL = "qwen2.5:7b"
# Default to 4096, but allow lower for 8GB VRAM cards
OLLAMA_CTXLEN = int(os.getenv("OLLAMA_CTXLEN", "4096"))
CHUNK_SIZE = 4000


def ensure_ollama_running():
    """Checks if Ollama is running and ensures model is available (auto-pulls if missing)."""
    global OLLAMA_MODEL
    try:
        # UPDATED: Increased timeout to 10s and forced 127.0.0.1 to avoid Windows localhost ipv6 issues
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"✅ Ollama is running. Available models: {models}")

            # Check for our preferred model
            if OLLAMA_MODEL not in models:
                # Try to find a fallback match (e.g. any qwen, any llama3, any mistral)
                fallback = next(
                    (
                        m
                        for m in models
                        if "qwen" in m or "llama" in m or "mistral" in m
                    ),
                    None,
                )

                if fallback:
                    print(
                        f"⚠️ Preferred model '{OLLAMA_MODEL}' not found. Using available fallback: '{fallback}'"
                    )
                    OLLAMA_MODEL = fallback
                    return True

                print(f"⚠️  Model '{OLLAMA_MODEL}' not found locally.")
                print(
                    f"⬇️  Auto-pulling '{OLLAMA_MODEL}' from Ollama library (this may take a while)..."
                )
                try:
                    # Stream the pull request to show progress
                    pull_resp = requests.post(
                        f"{OLLAMA_URL}/api/pull",
                        json={"name": OLLAMA_MODEL, "stream": True},
                        stream=True,
                        timeout=300,  # 5 min timeout for pull
                    )
                    pull_resp.raise_for_status()
                    for line in pull_resp.iter_lines():
                        if line:
                            data = json.loads(line)
                            status = data.get("status", "")
                            completed = data.get("completed", 0)
                            total = data.get("total", 1)
                            if total > 0:
                                percent = int((completed / total) * 100)
                                print(
                                    f"\rDownloading {OLLAMA_MODEL}: {status} {percent}%",
                                    end="",
                                    flush=True,
                                )
                            else:
                                print(
                                    f"\rDownloading {OLLAMA_MODEL}: {status}",
                                    end="",
                                    flush=True,
                                )
                    print(f"\n✅ Model '{OLLAMA_MODEL}' installed successfully.")
                except Exception as e:
                    print(f"\n❌ Failed to auto-pull model: {e}")
                    # Final fallback: just use the first available model if any exist
                    if models:
                        print(f"⚠️ Using first available model: '{models[0]}'")
                        OLLAMA_MODEL = models[0]
                        return True
                    return False
            return True
        else:
            msg = f"❌ Ollama returned status {response.status_code}"
            print(msg)
            raise ConnectionError(msg)

    except requests.exceptions.ConnectionError:
        print("⏳ Ollama not running. Attempting to start it...")

        # Try to start Ollama automatically
        import shutil
        import subprocess

        ollama_path = shutil.which("ollama")
        if ollama_path:
            try:
                # Start Ollama in the background
                print(f"🚀 Starting Ollama from {ollama_path}...")
                subprocess.Popen(
                    ["ollama", "serve"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    close_fds=True,
                )

                # Wait for it to spin up (up to 20 seconds)
                print("⏳ Waiting for Ollama to initialize...")
                for i in range(20):
                    time.sleep(1)
                    try:
                        if (
                            requests.get(
                                f"{OLLAMA_URL}/api/tags", timeout=2
                            ).status_code
                            == 200
                        ):
                            print("✅ Ollama started and connected successfully!")
                            return ensure_ollama_running()  # Recurse to check model
                    except Exception:
                        pass

            except Exception as e:
                print(f"❌ Failed to auto-start Ollama: {e}")
        else:
            print("❌ 'ollama' command not found in PATH.")

        # Final check after auto-start attempt
        msg = "❌ Ollama is NOT running (Connection Refused). Please check the console window that just opened, or start Ollama manually."
        print(msg)
        raise ConnectionError(msg)

    except Exception as e:
        msg = f"❌ Ollama check failed: {e}"
        print(msg)
        raise ConnectionError(msg)


def unload_model(model_name):
    """Explicitly unloads a model from VRAM to prevent OOM."""
    try:
        # Keep-alive 0 triggers immediate unload
        requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model_name, "keep_alive": 0},
            timeout=5,
        )
        print(f"👋 Unloaded model: {model_name} (Memory Freed)")
    except Exception as e:
        print(f"⚠️ Could not unload model {model_name}: {e}")


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


def snap_to_word_boundary(start, end, word_list, min_dur, max_dur):
    """
    Extends or trims timestamps to the nearest semantic boundary (., ?, !)
    to prevent mid-sentence cuts.
    """
    if not word_list:
        return start, end

    # Helper: Find word index close to a timestamp
    def find_idx(ts):
        closest_i = 0
        min_diff = float("inf")
        for i, w in enumerate(word_list):
            diff = abs(w["start"] - ts)
            if diff < min_diff:
                min_diff = diff
                closest_i = i
        return closest_i

    # 1. Snap END (Most Critical)
    # We want to finish the sentence. Look fast forward up to 8 seconds for a . or ?
    end_idx = find_idx(end)
    # original_end_idx = end_idx # Removed unused variable

    found_end = False
    # Look forward (extension) first - prefer finishing the thought
    for i in range(end_idx, min(len(word_list), end_idx + 15)):  # Look ahead 15 words
        w_text = word_list[i]["word"]
        if any(p in w_text for p in [".", "?", "!"]):
            new_end = word_list[i]["end"]
            # Only accept if within duration limits
            if (new_end - start) <= max_dur + 5.0:  # Allow 5s variance over max
                end = new_end
                found_end = True
                print(f"    ✨ Snapped END: Extended to finish sentence: '{w_text}'")
                break

    if not found_end:
        # Look backward (trim) if extension failed
        for i in range(end_idx, max(-1, end_idx - 10), -1):
            w_text = word_list[i]["word"]
            if any(p in w_text for p in [".", "?", "!"]):
                new_end = word_list[i]["end"]
                if (new_end - start) >= min_dur - 2.0:  # Allow 2s variance under min
                    end = new_end
                    found_end = True
                    print(f"    ✨ Snapped END: Trimmed to finish sentence: '{w_text}'")
                    break

    # 2. Snap START (Less Critical, usually AI gets this right)
    # But let's check if the previous word was a punctuation, meaning this is a fresh start
    start_idx = find_idx(start)
    # Ideally, word_list[start_idx-1] should end with punctuation.
    if start_idx > 0:
        prev_word = word_list[start_idx - 1]["word"]
        # If prev word didn't end sentence, maybe we started mid-sentence?
        # Try to find nearest previous sentence end
        if not any(p in prev_word for p in [".", "?", "!"]):
            # Look back to find a clean start
            for i in range(start_idx - 1, max(-1, start_idx - 10), -1):
                w_text = word_list[i]["word"]
                if any(p in w_text for p in [".", "?", "!"]):
                    # Found the end of previous sentence, so our start is i+1
                    new_start = word_list[i + 1]["start"]
                    if (end - new_start) <= max_dur + 5.0:
                        start = new_start
                        print("    ✨ Snapped START: Aligned to sentence start.")
                    break

    return start, end


def expand_context(start, end, word_list, min_sec):
    """
    Intelligently expands a clip to meet minimum duration requirements
    by adding surrounding sentences (context) rather than rejecting it.

    Args:
        start: Clip start time (seconds)
        end: Clip end time (seconds)
        word_list: Full list of word dicts with timestamps
        min_sec: Minimum duration required

    Returns:
        (new_start, new_end)
    """
    duration = end - start
    if duration >= min_sec:
        return start, end

    # We need to add at least (min_sec - duration) seconds
    needed = min_sec - duration
    print(
        f"    🧠 Expanding context: Clip is {duration:.1f}s (Min: {min_sec}s). Need +{needed:.1f}s."
    )

    # Find current indices in word list
    def find_idx(ts):
        closest_i = 0
        min_diff = float("inf")
        for i, w in enumerate(word_list):
            diff = abs(w["start"] - ts)
            if diff < min_diff:
                min_diff = diff
                closest_i = i
        return closest_i

    start_idx = find_idx(start)
    end_idx = find_idx(end)

    # Strategy: Alternating expansion (Prepend Sentence -> Append Sentence)
    # Prefer appending if we are mid-thought, prefer prepending if start is abrupt.
    # For simplicity, we try to grab the previous sentence first (Context), then next (continuation).

    # 1. Try PREPENDING previous sentence
    if start_idx > 0:
        # scan backwards for punctuation
        found_prev = False
        for i in range(start_idx - 1, max(-1, start_idx - 50), -1):
            w = word_list[i]
            if any(p in w["word"] for p in [".", "?", "!"]):
                # Found end of previous-previous sentence.
                # So the "previous" sentence starts at i+1
                new_start_idx = i + 1
                new_start = word_list[new_start_idx]["start"]
                added_dur = start - new_start
                start = new_start
                start_idx = new_start_idx
                duration += added_dur
                print(f"      Use PREV sentence: +{added_dur:.1f}s")
                found_prev = True
                break

        if not found_prev and start_idx > 0:
            # Just grab 5 seconds back if no sentence boundary found
            new_start = max(0, start - 5)
            duration += start - new_start
            start = new_start

    if duration >= min_sec:
        return start, end

    # 2. Try APPENDING next sentence
    if end_idx < len(word_list) - 1:
        found_next = False
        for i in range(end_idx + 1, min(len(word_list), end_idx + 50)):
            w = word_list[i]
            if any(p in w["word"] for p in [".", "?", "!"]):
                new_end = w["end"]
                added_dur = new_end - end
                end = new_end
                end_idx = i
                duration += added_dur
                print(f"      Use NEXT sentence: +{added_dur:.1f}s")
                found_next = True
                break

        if not found_next:
            new_end = min(word_list[-1]["end"], end + 5)
            duration += new_end - end
            end = new_end

    return start, end


def _build_system_prompt(content_type, min_sec, max_sec):
    """
    Builds content-type-aware system prompt for the LLM.

    Args:
        content_type: "podcast", "solo", or "auto"
        min_sec: Minimum clip duration
        max_sec: Maximum clip duration
    """
    # --- Shared rules (apply to ALL content types) ---
    shared_rules = (
        "RULES:\n"
        f"1. QUALITY OVER DURATION: Your primary goal is to find the BEST content. "
        f"   Target approx {min_sec}-{max_sec}s, but if a viral moment is slightly shorter or longer, output it anyway. "
        "   We will adjust the timing in post-processing.\n"
        "2. STRUCTURE: Ensure the clip has a clear HOOK (opening that grabs attention) and PAYOFF (satisfying conclusion). "
        "   Do NOT cut off mid-sentence or mid-thought.\n"
        "3. SCENE BOUNDARIES: Prefer cutting at Scene Boundaries if available.\n"
    )

    # --- Scoring criteria (shared) ---
    score_criteria = (
        "VIRALITY PROBABILITY SCORE (0-100%):\n"
        "   - This score represents the ESTIMATED PROBABILITY that this specific clip will go viral.\n"
        "   - 90-100: Very High Probability (Must Post). Contains a perfect hook and emotional payoff.\n"
        "   - 75-89: High Probability. Strong content that will perform well.\n"
        "   - < 75: Low Probability. Do NOT include.\n"
    )

    # --- Output format (shared) ---
    output_format = (
        "OUTPUT: Return ONLY valid JSON. "
        'Format: {"clips": [{"start": float, "end": float, "score": int, "hook": "string", "reason": "string", '
        '"suggested_emojis": ["emoji1", "emoji2"], "duration_type": "short_burst" | "story_mode"}]}'
    )

    if content_type == "podcast":
        system_prompt = (
            "You are an expert Video Editor specializing in clipping PODCAST and INTERVIEW content for viral Shorts/TikToks/Reels. "
            "Your goal is to find the MOST shareable, standalone moments from multi-speaker conversations. "
            "You understand that great podcast clips come from the DYNAMIC between speakers, not just one person talking.\n\n"
            + shared_rules
            + "4. CONTENT FILTER (PODCAST-SPECIFIC — CRITICAL):\n"
            "   ✅ KEEP (High Priority):\n"
            "      - 🔥 HEATED EXCHANGES: Disagreements, debates, or pushback between speakers\n"
            "      - 😲 REVELATION MOMENTS: 'Wait, you did WHAT?!' — shocking admissions or stories\n"
            "      - 😂 NATURAL HUMOR: Genuine laughs, witty comebacks, roasts, or awkward moments\n"
            "      - 💡 WISDOM DROPS: Calm but profound insights that make the viewer think deeply\n"
            "      - 🎤 STORY ARCS: A guest telling a compelling personal story with a clear beginning, tension, and payoff\n"
            "      - ❓ CONTRARIAN TAKES: 'Actually, that's completely wrong because...' — goes against popular opinion\n"
            "      - 🤯 UNEXPECTED CONTEXT: Surprising credentials, numbers, or background ('I was homeless, now I run a $100M company')\n"
            "   ❌ DISCARD (Low Viral Value):\n"
            "      - Small talk, pleasantries, or filler ('That's a great question', 'Yeah, absolutely')\n"
            "      - Overly technical jargon without emotional payoff\n"
            "      - Segments where only one person speaks in a dry, lecture-like monologue\n"
            "      - Sponsor reads, self-promotion, or 'make sure to subscribe'\n"
            "      - Incomplete exchanges where the conversation gets cut before the punchline or conclusion\n"
            "5. PODCAST-SPECIFIC SCORING BONUS:\n"
            "   - +10 points: Clip contains a genuine laugh or emotional reaction\n"
            "   - +10 points: Clip has a clear setup → punchline/reveal structure\n"
            "   - +5 points: Clip includes a quotable one-liner ('That's the problem with...', 'Here's what nobody tells you...')\n"
            "   - -15 points: Clip is just one person talking without any interaction\n"
            + score_criteria
            + output_format
        )
    elif content_type == "solo":
        system_prompt = (
            "You are an expert Video Editor for viral TikToks and Shorts (Alex Hormozi style). "
            "Your goal is to find the MOST engaging, standalone segments from the transcript that tell a complete mini-story. "
            "You have access to the transcript and (optionally) visual scene boundaries.\n\n"
            + shared_rules
            + "4. CONTENT FILTER (SOLO CONTENT — CRITICAL):\n"
            "   ✅ KEEP: Emotional realizations, strong opinions, contrarian views, funny moments, 'wait for it' builds, "
            "motivational calls-to-action, personal vulnerability, or data-backed claims.\n"
            "   ❌ DISCARD: Dry factual descriptions without emotional weight, generic intros ('Hello, welcome to...'), "
            "incomplete thoughts, or low-energy rambling.\n"
            + score_criteria
            + output_format
        )
    else:  # "auto" — let the LLM figure it out
        system_prompt = (
            "You are an expert Video Editor for viral TikToks, Shorts, and Reels. "
            "Your goal is to find the MOST engaging, standalone segments from the transcript. "
            "FIRST, determine if this is a PODCAST/INTERVIEW (multiple speakers) or SOLO content (single speaker), "
            "then apply the appropriate strategy:\n"
            "- For PODCASTS: Prioritize speaker dynamics — debates, reactions, humor, revelations, and exchanges.\n"
            "- For SOLO: Prioritize emotional hooks, story arcs, contrarian takes, and motivational moments.\n\n"
            + shared_rules
            + "4. CONTENT FILTER (CRITICAL):\n"
            "   ✅ KEEP: Heated exchanges, shocking revelations, genuine humor, emotional realizations, "
            "strong opinions, contrarian views, 'wait for it' builds, or profound wisdom drops.\n"
            "   ❌ DISCARD: Filler, small talk, generic intros, sponsor reads, dry monologues without payoff, "
            "incomplete thoughts, or low-energy segments.\n"
            + score_criteria
            + output_format
        )

    return system_prompt


def analyze_transcript(
    transcript_input,  # CHANGED: Can be text or word_list
    min_sec=30,
    max_sec=60,
    logger=None,
    video_path=None,
    progress_callback=None,
    content_type="auto",
):
    """
    Sends transcript to Ollama.
    Supports smart sematic snapping if transcript_input is a list of words.
    """
    # Validates Ollama connection (raises specific error if fails)
    ensure_ollama_running()

    # Handle Input Type
    word_list = []
    if isinstance(transcript_input, list):
        # We got raw words!
        word_list = transcript_input
        # Convert to text for LLM
        transcript_text = format_transcript_with_time(word_list)
    else:
        # Legacy string input
        transcript_text = str(transcript_input)
        word_list = []  # Can't do smart snapping without words

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
    except Exception:
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

            chunk_clips, _ = analyze_transcript(
                chunk_text,  # Passing text for chunks is safer/simpler for now
                min_sec,
                max_sec,
                logger,
                video_path=None,
                content_type=content_type,
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
        return unique_clips[:10], scenes  # Return top 10 and scenes

    # --- Existing Single-Chunk Logic ---

    system_prompt = _build_system_prompt(content_type, min_sec, max_sec)

    if logger:
        logger.log(f"📝 Content Type: {content_type.upper()}", "INFO", "GREY")

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
        "stream": True,
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

        # Retry logic for connection failures
        max_retries = 3
        retry_delay = 2
        response = None

        for attempt in range(max_retries):
            try:
                # Stream the response for progress feedback
                response = requests.post(
                    f"{OLLAMA_URL}/api/chat", json=payload, timeout=600, stream=True
                )
                response.raise_for_status()
                break  # Success, exit retry loop
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ) as conn_err:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)
                    msg = f"⚠️ Connection issue (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s..."
                    print(msg)
                    if logger:
                        logger.log(msg, "WARNING")
                    time.sleep(wait_time)
                else:
                    raise Exception(
                        f"Ollama connection failed after {max_retries} attempts: {conn_err}"
                    )

        # Stream response token by token for progress feedback
        response_text = ""
        token_count = 0
        analysis_start = time.time()
        last_progress_update = 0

        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                response_text += token
                token_count += 1

                # Update progress every ~20 tokens
                now = time.time()
                if now - last_progress_update >= 1.0:
                    elapsed = now - analysis_start
                    elapsed_str = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
                    status = f"🧠 AI Analyzing... {token_count} tokens ({elapsed_str} elapsed)"
                    print(f"\r{status}", end="", flush=True)
                    if progress_callback:
                        progress_callback(status)
                    last_progress_update = now

                # Check if done
                if chunk.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

        elapsed_total = time.time() - analysis_start
        elapsed_str = f"{int(elapsed_total // 60)}:{int(elapsed_total % 60):02d}"
        msg = f"\n✅ AI analysis complete ({token_count} tokens in {elapsed_str})"
        print(msg)
        if logger:
            logger.log(msg, "INFO", "GREEN")

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
                                # Standardize keys if LLM messed up
                                if "score" not in obj:
                                    obj["score"] = 70
                                extract = {
                                    k: v
                                    for k, v in obj.items()
                                    if k in ["start", "end", "score", "hook", "reason"]
                                }
                                extracted_clips.append(extract)
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
                    return [], []

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
                final_s, final_e = s_val, e_val

                # --- UNIFIED SMART SNAPPING & VALIDATION ---
                # 1. Apply Semantic Snapping FIRST (This may fix slightly short/long clips)
                if word_list:
                    # Snapping logic now handles the "intelligence" of finding the best cut
                    final_s, final_e = snap_to_word_boundary(
                        final_s, final_e, word_list, min_sec, max_sec
                    )

                    # --- CONTEXT EXPANSION (NEW) ---
                    # If clip is too short, intelligently add surrounding sentences
                    curr_dur = final_e - final_s
                    if curr_dur < min_sec:
                        final_s, final_e = expand_context(
                            final_s, final_e, word_list, min_sec
                        )
                    # -------------------------------

                # 2. Check Duration (AFTER Snapping)
                final_dur = final_e - final_s

                # 3. Handle Too Long (Split Strategy)
                if final_dur > max_sec + 5.0:
                    print(
                        f"⚠️ Clip too long ({final_dur:.1f}s). Splitting into parts..."
                    )
                    # Example: 155s -> Part 1 (0-60), Part 2 (60-120), Part 3 (120-155)
                    # We need to be smart about overlapping or strict splitting.
                    # Let's try strict sequential splitting for now, as that's safer.

                    current_start = final_s
                    part_num = 1

                    while current_start < final_e:
                        # Target end is start + max_sec
                        target_end = min(current_start + max_sec, final_e)

                        # If the remaining part is too short (< min_sec), we might skip or merge
                        if (target_end - current_start) < min_sec:
                            break

                        # Create sub-clip
                        sub_clip = x.copy()
                        sub_clip["start"] = current_start
                        sub_clip["end"] = target_end
                        sub_clip["duration_type"] = "split_part"
                        sub_clip["hook"] = f"{x.get('hook', '')} (Part {part_num})"

                        clips.append(sub_clip)
                        current_start = target_end
                        part_num += 1

                # 4. Handle Valid Clip
                elif final_dur >= min_sec - 5.0:  # Allow slightly under min
                    # Update the clip with snapped values
                    x["start"] = final_s
                    x["end"] = final_e
                    x["score"] = int(score) if score else 70
                    clips.append(x)

        # Sort by Score
        clips.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_clips = clips[:5]

        # --- VISION ANALYSIS (Hybrid Scoring) ---
        if video_path and os.path.exists(video_path):
            try:
                # 1. UNLOAD TEXT MODEL FIRST (Critical for 8GB VRAM)
                if logger:
                    logger.log(
                        f"👋 Unloading {OLLAMA_MODEL} to free VRAM for Vision...",
                        "INFO",
                        "GREY",
                    )
                unload_model(OLLAMA_MODEL)
                time.sleep(1)  # Brief pause for VRAM cleanup

                msg = f"👁️ Analyzing Visuals for Top {len(top_clips)} Clips..."
                print(msg)
                if logger:
                    logger.log(msg, "INFO", "PURPLE")

                # Use minicpm-v for efficiency (default)
                VISION_MODEL = "minicpm-v"
                vision = VisionAnalyzer(model_name=VISION_MODEL)

                # OPTIMIZATION: Open Video Capture ONCE
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise Exception(f"Could not open video: {video_path}")

                try:
                    # We only analyze the specific time ranges of the top clips to save time/compute
                    for clip in top_clips:
                        # Multi-Frame Analysis (Start, Mid, End)
                        timestamps = [
                            clip["start"] + (clip["end"] - clip["start"]) * 0.1,
                            clip["start"] + (clip["end"] - clip["start"]) * 0.5,
                            clip["start"] + (clip["end"] - clip["start"]) * 0.9,
                        ]

                        frame_scores = []

                        for i, ts in enumerate(timestamps):
                            # Quick frame extraction (seek)
                            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
                            ret, frame = cap.read()

                            if ret:
                                temp_frame = f"temp_frame_{i}_{ts:.2f}.jpg"
                                cv2.imwrite(temp_frame, frame)

                                prompt = 'Rate this video frame for viral potential (0-100). Is it visually interesting? JSON: {"score": int}'
                                try:
                                    response_text = vision.analyze_frame(
                                        temp_frame, prompt
                                    )
                                    # Basic cleanup
                                    clean = (
                                        response_text.replace("```json", "")
                                        .replace("```", "")
                                        .strip()
                                    )
                                    if "{" in clean:
                                        import json as j

                                        v_data = j.loads(clean)
                                        frame_scores.append(int(v_data.get("score", 0)))
                                except Exception:
                                    pass
                                finally:
                                    if os.path.exists(temp_frame):
                                        os.remove(temp_frame)

                        # Calculate Weighted Visual Score
                        # If we have 3 scores: Start(20%), Mid(50%), End(30%)
                        if frame_scores:
                            if len(frame_scores) >= 3:
                                visual_score = int(
                                    frame_scores[0] * 0.2
                                    + frame_scores[1] * 0.5
                                    + frame_scores[2] * 0.3
                                )
                            else:
                                visual_score = int(
                                    sum(frame_scores) / len(frame_scores)
                                )
                        else:
                            visual_score = 0

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
                finally:
                    # ALWAYS release the capture
                    cap.release()
                    # ALWAYS unload vision model
                    if logger:
                        logger.log(f"👋 Unloading {VISION_MODEL}...", "INFO", "GREY")
                    unload_model(VISION_MODEL)

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
        return top_clips, scenes

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()

        msg = f"❌ Analysis Error: {e}"
        print(msg)
        # print(f"\n{'=' * 60}\nDETAILED ERROR:\n{'=' * 60}\n{error_trace}\n{'=' * 60}\n")

        if logger:
            logger.error(msg)
            logger.log(f"Error Type: {type(e).__name__}", "ERROR")
            logger.log(f"Error Details: {str(e)}", "ERROR")
            # Log the full traceback to file
            for line in error_trace.split("\n"):
                if line.strip():
                    logger.log(line, "ERROR")

        # If possible, show what failed
        # if "response_text" in locals() and response_text:
        #    if logger:
        #        logger.log(f"Raw Ollama Output: {response_text[:500]}", "INFO")

        return [], scenes

    finally:
        # CRITICAL: Always unload model to free VRAM for rendering
        # Note: Vision model is unloaded in its own block, but we ensure text model is gone too.
        unload_model(OLLAMA_MODEL)


if __name__ == "__main__":
    # Test block
    mock_text = (
        "[0.0s] This is a test [5.0s] for a viral video [10.0s] that we are making."
    )
    clips, scenes = analyze_transcript(mock_text)
    print(f"Clips: {clips}")
    print(f"Scenes: {scenes}")
