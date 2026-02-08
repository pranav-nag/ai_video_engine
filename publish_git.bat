@echo off
TITLE AI Video Engine - Publish to GitHub
COLOR 0A

echo ==================================================
echo    AI VIDEO ENGINE - GITHUB PUBLISHER (RECOVERY MODE)
echo ==================================================
echo.

:: Check if git exists
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git is not installed. Please install Git for Windows.
    pause
    exit /b
)

:: Check if repo exists, if not, init
if not exist ".git" (
    echo ⚠️  Git repository not found (Did you delete .git?)
    echo 🔧 Re-initializing repository...
    git init
    git add .
    git commit -m "Recovered project state"
)

echo.
echo This script will help you push your code to GitHub.
echo.

set REPO_URL=https://github.com/pranav-nag/ai_video_engine.git
echo [INFO] Using Repository: %REPO_URL%

echo.
echo [STEP 1] Configuring Remote...
git remote remove origin 2>NUL
git remote add origin %REPO_URL%

echo.
echo [STEP 2] Fetching & Merging Remote Changes...
echo (If prompted for a merge message, just close the editor or press :q!)
git pull origin main --allow-unrelated-histories

echo.
echo [STEP 3] Pushing to GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Push failed.
    echo 1. Check if you are signed in (Credential Manager).
    echo 2. If 2FA is on, use a Personal Access Token password.
    pause
    exit /b
)

echo.
echo ✅ SUCCESS! Code pushed to:
echo %REPO_URL%
echo.
pause
exit /b
