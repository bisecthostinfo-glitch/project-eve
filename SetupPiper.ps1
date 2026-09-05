# SetupPiper.ps1
# Installs piper-tts and downloads a natural-sounding local voice model.
# Run in PowerShell from the project root: powershell -ExecutionPolicy Bypass -File SetupPiper.ps1

Write-Host "Installing piper-tts..."
pip install piper-tts

Write-Host "Downloading voice model: en_US-lessac-medium (natural-sounding, good default)"
python -m piper.download_voices en_US-lessac-medium --download-dir "Data\PiperVoices"

Write-Host ""
Write-Host "Done. Voice files are in Data\PiperVoices"
Write-Host "Other voices worth trying (swap the name in Config.py / config.json):"
Write-Host "  en_US-ryan-high        - higher quality male voice, slower to synthesize"
Write-Host "  en_US-hfc_female-medium - female voice"
Write-Host "Full list: https://github.com/rhasspy/piper/blob/master/VOICES.md"
