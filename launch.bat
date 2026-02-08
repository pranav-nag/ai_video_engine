@echo off
:: Fix encoding so logs are readable
chcp 65001 > NUL
cd /d "E:\AI_Video_Engine"

set "APP_NAME=AI Video Engine PRO"
title %APP_NAME%

echo ---------------------------------------
echo  %APP_NAME% - Launching...
echo ---------------------------------------

:: 1. Set Environment Variables
set "HF_HOME=E:\AI_Video_Engine\cache\huggingface"
set "OLLAMA_MODELS=E:\AI_Video_Engine\cache\ollama"
set "TORCH_HOME=E:\AI_Video_Engine\cache\torch"
set "TEMP=E:\AI_Video_Engine\temp"
set "TMP=E:\AI_Video_Engine\temp"
set "PYTHONPATH=E:\AI_Video_Engine"

:: 2. Check for Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv folder is missing. 
    echo Please run 'install.bat' first.
    pause
    exit /b
)

:: 3. Activate Python Environment
call .venv\Scripts\activate

:: 4. Start Ollama (Silent Background)
:: We use powershell to start it truly hidden
echo ⚙️  Starting/Checking Ollama Server (Hidden)...
powershell -WindowStyle Hidden -Command "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
timeout /t 5 > NUL

:: 5. Launch the App
echo 🚀 Launching Premium GUI...
python -m src.main_ui

echo.
echo 🏁 App session ended.
echo Check the 'logs' folder for detailed history.
pause