@echo off
cd /d "E:\AI_Video_Engine"

:: 1. Force Windows Temp to E: drive for this session (Safety for C: drive)
set TMP=E:\AI_Video_Engine\temp
set TEMP=E:\AI_Video_Engine\temp

:: 2. Create Virtual Environment
echo Creating Virtual Environment...
python -m venv .venv

:: 3. Activate Virtual Environment
echo Activating .venv...
call .venv\Scripts\activate

:: 4. Install PyTorch (CUDA 12.1 for RTX 4060)
:: Using --cache-dir to ensure downloads go to E:
echo Installing PyTorch (This may take a while)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --cache-dir "E:\AI_Video_Engine\cache\pip_temp"

:: 5. Install Requirements
echo Installing dependencies...
pip install -r requirements.txt --cache-dir "E:\AI_Video_Engine\cache\pip_temp"

echo.
echo ========================================================
echo  Setup Complete!
echo  All caches and temp files routed to E:\AI_Video_Engine
echo ========================================================
pause