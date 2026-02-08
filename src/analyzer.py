import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# UPDATED: Matches your 'ollama list' output
OLLAMA_MODEL = "llama3.2:latest"
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


def analyze_transcript(transcript_text, min_sec=15, max_sec=60):
    """
    Sends transcript to Ollama.
    Handles long transcripts by splitting them into chunks if they exceed token limits.
    """
    if not ensure_ollama_running():
        return []

    # --- NEW: Chunking Logic for Long Videos ---
    # Max words per AI request (approx 8-10 mins of speech)
    MAX_WORDS_PER_CHUNK = 1500
    words = transcript_text.split()

    if len(words) > MAX_WORDS_PER_CHUNK:
        print(f"📦 Transcript is long ({len(words)} words). Processing in chunks...")
        all_clips = []

        # Process in chunks with 10% overlap (to catch clips on boundaries)
        step = int(MAX_WORDS_PER_CHUNK * 0.9)
        for i in range(0, len(words), step):
            chunk_text = " ".join(words[i : i + MAX_WORDS_PER_CHUNK])
            print(f"🎬 Analyzing Chunk {i // step + 1}...")
            chunk_clips = analyze_transcript(chunk_text, min_sec, max_sec)
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
        "RULES:\n"
        f"1. EXTREMELY IMPORTANT: Each clip MUST be between {min_sec} and {max_sec} seconds long. "
        f"2. DO NOT output clips shorter than {min_sec} seconds. "
        "3. Ensure the clip has a complete thought (starts and ends with a full sentence). "
        "4. Score clips (0-100) based on: Hook strength, Coherence, and Viral Potential. "
        "5. Return ONLY valid JSON. "
        'Format: {"clips": [{"start": float, "end": float, "score": int, "hook": "string", "reason": "string"}]}'
    )

    # Payload for /api/chat
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Analyze this transcript and find 3-5 viral clips ({min_sec}-{max_sec}s):\n{transcript_text}",
            },
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.7,  # Slightly creative but focused
            "num_ctx": 4096,  # Ensure enough context for long videos
        },
    }

    try:
        print(f"🧠 AI is analyzing for viral clips (using {OLLAMA_MODEL})...")
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()

        result = response.json()
        response_text = result.get("message", {}).get("content", "")

        try:
            # 1. First, try simple decode
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # 2. Robust Regex Extraction for Multiple JSON Objects
            import re

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
                # [NEW] Duration Validation
                duration = e_val - s_val
                if duration < 10:
                    print(
                        f"⚠️ Skipping short clip ({duration:.1f}s): {x.get('hook', 'Unknown')}"
                    )
                    continue

                # Force to float/int
                try:
                    cleaned_clip = {
                        "start": s_val,
                        "end": e_val,
                        "score": int(score) if safe_float(score) is not None else 0,
                        "hook": str(x.get("hook", "No Hook")),
                        "reason": str(x.get("reason", "No reason provided")),
                    }
                    clips.append(cleaned_clip)
                except (ValueError, TypeError):
                    continue

        # Sort by score (Robustly)
        clips.sort(key=lambda x: x["score"], reverse=True)

        print(f"🔥 AI successfully found {len(clips)} clips.")
        return clips[:5]

    except Exception as e:
        print(f"❌ Analysis Error: {e}")
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
