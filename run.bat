@echo off
setlocal enabledelayedexpansion
TITLE AI Video Engine - Build & Launch

echo ========================================
echo 🚀 AI Video Engine - Unified Run Script
echo ========================================

:: 1. Cleanup old processes to unlock files
echo.
echo 🛑 Step 1: Closing existing instances...
taskkill /F /IM "AI Video Engine.exe" /T 2>nul
taskkill /F /IM "python.exe" /T 2>nul
taskkill /F /IM "electron.exe" /T 2>nul
timeout /t 1 /nobreak >nul

:: 2. Ensure virtual environment exists
if not exist ".venv" (
    echo.
    echo 🔧 Virtual environment not found. Please run:
    echo    python -m venv .venv
    echo    .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: 3. Build and Package (Fast Mode)
echo.
echo 🛠️  Step 2: Building and Packaging App...
:: npm run build:fast already handles frontend build + electron packaging
call npm run build:fast

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Build failed. Check the errors above.
    pause
    exit /b %ERRORLEVEL%
)

:: 4. Launch the built executable
set "APP_PATH=electron\dist\win-unpacked\AI Video Engine.exe"
echo.
if exist "%APP_PATH%" (
    echo 🚀 Step 3: Launching AI Video Engine...
    echo ✨ Happy Clip Making!
    start "" "%APP_PATH%"
) else (
    echo ❌ Error: Built app not found at %APP_PATH%
    pause
)
