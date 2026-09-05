@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Install it from https://python.org/downloads
    echo ^(check "Add python.exe to PATH" during install^), then run this again.
    pause
    exit /b 1
)

if not exist "Data\.deps_installed" (
    echo First run detected - installing dependencies, this can take a few minutes...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency install failed - see errors above.
        pause
        exit /b 1
    )
    if not exist "Data" mkdir "Data"
    echo ok > "Data\.deps_installed"
)

echo Starting Personal Assistant...
python Gui.py

if errorlevel 1 (
    echo.
    echo The app closed with an error - see above.
    pause
)
