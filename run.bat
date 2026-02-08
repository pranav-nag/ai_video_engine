@echo off
TITLE AI Video Engine - DEV MODE
COLOR 0A

:: Check for virtual environment
if not exist ".venv" (
    echo ❌ Virtual environment not found!
    echo    Please run: python -m venv .venv
    pause
    exit /b
)

:: Run the app using the python in .venv
echo 🚀 Launching AI Video Engine (Dev Mode)...
.venv\Scripts\python src\bootstrap.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ App crashed or closed with error.
    pause
)
