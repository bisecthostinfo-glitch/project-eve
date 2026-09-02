# BuildExe.ps1
# Packages Main.py into a single Windows .exe using PyInstaller.
# Run in PowerShell from the project root: powershell -ExecutionPolicy Bypass -File BuildExe.ps1

Write-Host "Installing PyInstaller..."
pip install pyinstaller

Write-Host "Building PersonalAssistant.exe..."
pyinstaller --onefile --name PersonalAssistant --console Main.py `
    --add-data "Tools;Tools" `
    --add-data "Providers;Providers"

Write-Host ""
Write-Host "Done. Find it at dist\PersonalAssistant.exe"
Write-Host ""
Write-Host "Note: config.json, .env, credentials.json, and token.json are NOT"
Write-Host "bundled into the exe (they're gitignored/user-specific on purpose)."
Write-Host "Keep them next to the exe in the same folder, or set env vars"
Write-Host "(ANTHROPIC_API_KEY, LLM_PROVIDER, etc.) before running it."
