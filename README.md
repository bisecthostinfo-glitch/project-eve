# Personal AI Assistant

Voice-capable personal assistant with LLM tool-calling access to Calendar,
Google Workspace, local files, email, Discord, and OS/app control.

Guardrails are minimal by design: no content filtering, but confirmation is
required before delete, send, purchase, download, or any irreversible
action. Every tool call is logged.

## Status: Milestone 2 — write actions

Implemented (Milestone 1 +):
- `Tools/CalendarCreateEvent.py` — creates Google Calendar events (OAuth
  wiring still pending, Milestone 3). `IsDestructive = True`, so the loop's
  confirmation checkpoint fires before it runs.
- `Tools/FileManager.py` — Move / Rename / Delete / Extract, scoped to
  `ScopedDirectories` from config. Extracts .zip natively, .7z via `py7zr`,
  .rar via `rarfile` (needs `unrar`/`UnRAR.exe` on PATH — see note below).
  `IsDestructive = True`.
- `FileSearch` content indexing expanded beyond filenames to
  .log/.yaml/.yml/.ini/.xml in addition to .txt/.md/.py/.json/.csv.

## Building a standalone .exe

Run `BuildExe.ps1` — it installs PyInstaller and packages `Main.py` into
`dist\PersonalAssistant.exe`. Config, `.env`, and any OAuth tokens are
**not** bundled (deliberately — they're per-user secrets); keep them in
the same folder as the exe, or set the equivalent environment variables
before running it.

`.rar` extraction needs the real `unrar` binary on PATH, separate from the
`rarfile` Python package — on Windows, grab `UnRAR.exe` from
rarlab.com/rar_add.htm and put it next to the exe or add it to PATH. If
it's missing, `FileManager` reports a clear error instead of failing silently.

## Setup

### Option A — Claude (Anthropic API)

```
pip install -r requirements.txt
cp .env.example .env   # fill in your own key, then export it
export ANTHROPIC_API_KEY=...
python Main.py
```

### Option B — Local model via Ollama

Windows: run `SetupOllama.ps1` (installs Ollama via winget, pulls
`qwen2.5:7b`, verifies the server is up). macOS/Linux: install Ollama from
ollama.com, then `ollama pull qwen2.5:7b`.

```
pip install -r requirements.txt
set LLM_PROVIDER=ollama          # PowerShell: $env:LLM_PROVIDER = "ollama"
python Main.py
```

Or set `"LlmProvider": "ollama"` in `config.json` instead of using the env
var. `LLM_PROVIDER` / `OLLAMA_MODEL` / `OLLAMA_BASE_URL` env vars override
`config.json` if both are set.

The LLM backend is abstracted in `Providers/` (`AnthropicProvider.py`,
`OllamaProvider.py`) behind a normalized message-block format, so
`AgentLoop.py` doesn't care which one is active. Tool-calling reliability
varies a lot across local models — worth testing your actual tool chains
(2-3 step requests) before committing to one for daily use.

`config.json` (gitignored) overrides `Config.DefaultConfig` — copy the
`ScopedDirectories` / `ToolFlags` shape from `Config.py` if you want to
customize before Milestone 3 adds a proper setup flow.

## Roadmap

1. Text prototype + bounded loop — done
2. Write actions: CalendarCreateEvent, FileManager, confirmation + logging pattern — **current**
3. Google Workspace: DriveSearch, SheetsAccess, GmailAccess, PhotosSearch, GoogleXFileDedup, unified search
4. SystemControl
5. DownloadManager + AutoWriting
6. Discord (bot-in-servers first; client-token approach flagged as ToS risk)
7. Memory layer (SQLite/Postgres persistent facts + retrieval)
8. Voice input (Whisper/cloud STT, push-to-talk)
9. Voice output (Piper/cloud TTS)
10. Wake word + speaker recognition
11. Reliability pass

## Security notes

- Never commit `config.json`, `.env`, `credentials.json`, `token.json`, or
  any OAuth token / API key. All are gitignored.
- OAuth tokens for Google/Discord must be stored encrypted locally.
- `FileSearch` / `FileManager` / `SystemControl` are scoped to directories
  listed in config, not the whole filesystem.
