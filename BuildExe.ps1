# BuildExe.ps1
# Packages Gui.py into a single windowed Windows .exe using PyInstaller.
# This is the primary app launcher — no console window, shows the setup
# wizard on first run if no provider is configured yet.
# Run in PowerShell from the project root: powershell -ExecutionPolicy Bypass -File BuildExe.ps1

Write-Host "Installing PyInstaller..."
pip install pyinstaller

Write-Host "Building PersonalAssistant.exe (this can take a few minutes — bundles faster-whisper/piper)..."
pyinstaller --onefile --windowed --name PersonalAssistant Gui.py `
    --add-data "Tools;Tools" `
    --add-data "Providers;Providers" `
    --collect-all faster_whisper `
    --collect-all piper `
    --collect-all ctranslate2

Write-Host ""
Write-Host "Done. Find it at dist\PersonalAssistant.exe"
Write-Host ""
Write-Host "This is now the main launcher: double-click it to open the app."
Write-Host "First run shows a setup screen (pick Claude or Ollama, enter your"
Write-Host "API key if using Claude) — everything's saved encrypted next to"
Write-Host "the exe in a Data\ folder, so you won't see that screen again."
Write-Host ""
Write-Host "Voice: run SetupPiper.ps1 once beforehand if you want TTS, and set"
Write-Host "'VoiceEnabled': true in config.json (create it next to the exe if"
Write-Host "it doesn't exist yet — copy the shape from Config.py's DefaultConfig)."
Write-Host ""
Write-Host "If the exe fails to start with a missing-module error, faster-whisper"
Write-Host "or piper likely has a native dependency PyInstaller didn't catch —"
Write-Host "re-run with an extra --collect-all <missing-package-name> and rebuild."
