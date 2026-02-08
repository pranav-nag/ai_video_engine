import os

def create_structure():
    # 1. Define Base Path
    base_path = r"E:\AI_Video_Engine"
    
    # 2. Define Folder Structure
    folders = [
        r"assets\fonts",
        r"assets\overlays",
        r"cache\huggingface",
        r"cache\ollama",
        r"cache\pip_temp",
        r"cache\torch",
        r"temp",
        r"output",
        r"src"
    ]

    print(f"🚀 Initializing Project at: {base_path}...\n")

    # Create Folders
    for folder in folders:
        full_path = os.path.join(base_path, folder)
        try:
            os.makedirs(full_path, exist_ok=True)
            print(f"✅ Created: {full_path}")
        except Exception as e:
            print(f"❌ Error creating {full_path}: {e}")

    # 3. Generate .env file
    # Note: We use forward slashes for env vars as they are safer for Python libraries
    # and avoid escape character issues in string parsing.
    env_content = (
        f"HF_HOME={base_path.replace(os.sep, '/')}/cache/huggingface\n"
        f"OLLAMA_MODELS={base_path.replace(os.sep, '/')}/cache/ollama\n"
        f"TORCH_HOME={base_path.replace(os.sep, '/')}/cache/torch\n"
        f"XDG_CACHE_HOME={base_path.replace(os.sep, '/')}/cache\n"
        f"TEMP={base_path.replace(os.sep, '/')}/temp\n"
    )
    
    env_path = os.path.join(base_path, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f"✅ Generated: {env_path}")

    # 4. Generate requirements.txt
    requirements = [
        "faster-whisper",
        "yt-dlp",
        "moviepy",
        "opencv-python",
        "mediapipe",
        "flet",
        "python-dotenv",
        "colorama",
        "requests",
        "psutil"
    ]
    
    req_path = os.path.join(base_path, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("\n".join(requirements))
    print(f"✅ Generated: {req_path}")

    # 5. Print BAT file content
    pip_cache_path = os.path.join(base_path, "cache", "pip_temp")
    temp_path = os.path.join(base_path, "temp")
    
    print("\n" + "="*60)
    print("👇 COPY THE CONTENT BELOW AND SAVE AS 'install.bat' 👇")
    print("   (Save it inside E:\\AI_Video_Engine\\)")
    print("="*60 + "\n")

    bat_content = f"""@echo off
cd /d "{base_path}"

:: 1. Force Windows Temp to E: drive for this session (Safety for C: drive)
set TMP={temp_path}
set TEMP={temp_path}

:: 2. Create Virtual Environment
echo Creating Virtual Environment...
python -m venv .venv

:: 3. Activate Virtual Environment
echo Activating .venv...
call .venv\\Scripts\\activate

:: 4. Install PyTorch (CUDA 12.1 for RTX 4060)
:: Using --cache-dir to ensure downloads go to E:
echo Installing PyTorch (This may take a while)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --cache-dir "{pip_cache_path}"

:: 5. Install Requirements
echo Installing dependencies...
pip install -r requirements.txt --cache-dir "{pip_cache_path}"

echo.
echo ========================================================
echo  Setup Complete! 
echo  All caches and temp files routed to E:\\AI_Video_Engine
echo ========================================================
pause
"""
    print(bat_content)
    print("="*60)

if __name__ == "__main__":
    create_structure()