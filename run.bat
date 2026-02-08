@echo off
SETLOCAL EnableDelayedExpansion
TITLE AI Video Engine - DEV MODE
COLOR 0A

:: Check for virtual environment
if not exist ".venv" (
    echo ⚠️  Virtual environment not found!
    echo 🔧 Creating virtual environment and installing requirements...
    python -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Failed to create virtual environment. 
        echo    Make sure Python is installed and in your PATH.
        pause
        exit /b
    )
    echo ⬇️  Installing dependencies...
    .venv\Scripts\python -m pip install --upgrade pip
    .venv\Scripts\python -m pip install -r requirements.txt
    echo ✅ Setup Complete.
)

:: Run the app
echo 🚀 Launching AI Video Engine...
.venv\Scripts\python -m src.bootstrap

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ App exited with an error.
    pause
)
