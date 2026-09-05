# Personal AI Assistant

Voice-capable personal assistant with LLM tool-calling access to Calendar,
Google Workspace, local files, email, Discord, and OS/app control.

Guardrails are minimal by design: no content filtering, but confirmation is
required before delete, send, purchase, download, or any irreversible
action. Every tool call is logged.

## Status: In-app Settings + fixed network map

- `SettingsWindow.py` — gear icon in the main window opens it. Toggle
  voice input and AI voice output separately (voice changes need a
  restart, shown in-window), edit the system prompt live (applies
  immediately, no restart), and set an activation phrase — reserved for
  future wake-word support, not wired to a listener yet, doesn't affect
  push-to-talk.
- `NetworkMap.py` rebuilt: tool names were overflowing their circles
  (`CalendarCreateEvent` wrapping into 3 lines). Now each tool is a small
  dot with its label beside it instead of text crammed inside a circle —
  scales to any tool name length.
- `Config.py`: `VoiceEnabled` split into `VoiceInputEnabled` /
  `VoiceOutputEnabled` so mic and speech-out can be toggled independently.
  Added `ActivationPhrase` (currently just stored, not yet functional).

## Status: Modern UI + one-click launcher

- Rebuilt `Gui.py` on `customtkinter` — dark theme, rounded buttons/cards,
  proper chat bubbles instead of a plain text box. `SetupWizard.py`
  matches the same look.
- Added `NetworkMap.py` — a live node graph on the right side: You → AI →
  one node per active tool. When the assistant actually calls a tool
  mid-request, that node and its connecting line light up green in real
  time (wired through a new `OnToolCall` callback on `AgentLoop`), so you
  can see what it's doing while it's doing it, not just the final answer.
- `RunAssistant.bat` — double-click launcher. Installs dependencies on
  first run only (marked via `Data\.deps_installed`, gitignored), then
  launches `Gui.py` every time after. This assumes you've already cloned
  the repo once (private repo, so that first clone still needs your own
  auth) — this script is for "run it" from that point on, not the
  from-scratch clone step.

## Status: Real app launcher — setup wizard + windowed exe

`Gui.py` is now the actual entry point/launcher, not just a chat window:
- On first run (no `config.json`, or Claude selected with no API key
  stored), it shows a `SetupWizard` — pick Claude or Ollama, paste an API
  key if using Claude. Saved encrypted via `SecretsStore.py` (same Fernet
  pattern as the Google OAuth token), so the key never sits in plaintext.
- After that, it goes straight to the chat window every time.
- `BuildExe.ps1` now packages `Gui.py` with `--windowed` (no console
  popup) as `PersonalAssistant.exe` — double-click it, that's the app.

`SecretsStore.py` is a small generic encrypted key-value store — `Get`/
`Set`/`Has` on any string key, backed by `Data/secrets.enc` +
`Data/secrets.key` (both gitignored). `ANTHROPIC_API_KEY` env var still
overrides it if set, for anyone who wants to run headless/scripted.

`Main.py` (the old text-only CLI) still works standalone if you want it,
but `Gui.py` is the one meant for actually launching the app now.

## Status: Core interface — GUI + voice (STT/TTS), ahead of the milestone order

Priorities got reordered on request: interface + voice came before finishing
Google Workspace (Milestone 3 was built, then reverted — see git history —
to focus here first). Implemented:

- `Gui.py` — simple Tkinter window: chat log, text entry, Send button,
  hold-to-talk button (appears only if voice is enabled and set up
  correctly), Mute checkbox. Will very likely get replaced/reworked later —
  built to be functional, not final.
- `AudioRecorder.py` — push-to-talk recording via `sounddevice`, 16kHz
  mono float32 for Whisper.
- `SpeechToText.py` — `faster-whisper` wrapper, `base.en` model by
  default (downloads automatically on first use).
- `TextToSpeech.py` — Piper wrapper (local neural TTS, natural-sounding
  vs. robotic SAPI voices), plays audio directly via `sounddevice`.
- `SetupPiper.ps1` — installs `piper-tts` and downloads the
  `en_US-lessac-medium` voice model.

To enable voice: run `SetupPiper.ps1` once, then open Settings in the app
(gear icon, bottom right) and turn on "voice input" and/or "AI voice
output". Restart the app after saving — voice setup happens at startup.
"Hold to Talk" appears once voice input is on.

Milestone 2 (write actions) below is still complete and unaffected by this
reordering.

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

### Recommended — the app launcher

After cloning the repo once, just double-click `RunAssistant.bat` from
then on — it installs dependencies the first time only, then launches the
app every time. Manual equivalent:

```
pip install -r requirements.txt
python Gui.py
```

First run shows a setup screen: pick Claude or Ollama, paste your API key
if using Claude. Everything after that just opens the chat window
directly. This is also what `BuildExe.ps1` packages into
`PersonalAssistant.exe`.

### Manual / scripted — text-only CLI

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
