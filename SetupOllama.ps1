# SetupOllama.ps1
# Auto-installs Ollama on Windows and pulls a tool-calling-capable model.
# Run in PowerShell: powershell -ExecutionPolicy Bypass -File SetupOllama.ps1

Write-Host "Checking for winget..."
$WingetExists = Get-Command winget -ErrorAction SilentlyContinue

if (-not $WingetExists) {
    Write-Host "winget not found. Install App Installer from the Microsoft Store, then re-run this script."
    exit 1
}

Write-Host "Installing Ollama..."
winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements

Write-Host "Waiting for Ollama service to start..."
Start-Sleep -Seconds 5

# Ollama installs itself as a background service and adds 'ollama' to PATH,
# but PATH changes need a fresh shell to take effect in some cases.
$OllamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $OllamaCmd) {
    Write-Host "ollama command not found in this session. Close and reopen PowerShell, then re-run this script."
    exit 1
}

Write-Host "Pulling model: qwen2.5:7b (good tool-calling support, ~4.7GB, runs on most modern GPUs/CPUs)"
ollama pull qwen2.5:7b

Write-Host "Verifying server is responding..."
$Response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get
Write-Host "Installed models:"
$Response.models | ForEach-Object { Write-Host " - $($_.name)" }

Write-Host ""
Write-Host "Done. Ollama is running at http://localhost:11434"
Write-Host "Set this in your environment before running Main.py:"
Write-Host '  $env:LLM_PROVIDER = "ollama"'
Write-Host '  $env:OLLAMA_MODEL = "qwen2.5:7b"'
