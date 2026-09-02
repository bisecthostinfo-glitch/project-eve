# Personal AI Assistant

Voice-capable personal assistant with LLM tool-calling access to Calendar,
Google Workspace, local files, email, Discord, and OS/app control.

Guardrails are minimal by design: no content filtering, but confirmation is
required before delete, send, purchase, download, or any irreversible
action. Every tool call is logged.

## Status: Milestone 3 — Google Workspace

Implemented (Milestone 1-2 +):
- `GoogleAuth.py` — one OAuth flow, scoped for Calendar/Drive/Gmail/Sheets.
  Token stored encrypted at rest (`Data/token.enc`, `Data/token.key` —
  both gitignored) rather than plaintext, using `cryptography`'s Fernet.
- `Tools/DriveSearch.py` — searches Drive by name/content, then filters
  out anything that already exists locally via `GoogleXFileDedup.py`
  (runs as a step inside DriveSearch, not a separate registered tool).
- `Tools/SheetsAccess.py` — Read/Write specific ranges. Write requires
  confirmation.
- `Tools/GmailAccess.py` — Search/Read/Draft/Send. The whole tool is
  gated behind confirmation (not just Send) to keep the confirmation
  logic simple; split Search/Read into a separate low-risk tool later if
  the extra prompts get annoying.
- `CalendarLookup`/`CalendarCreateEvent` now actually wire up to a real
  Calendar service using the same shared credentials, instead of the
  `None` placeholder from Milestones 1-2.

**Blocked, not built: PhotosSearch.** Google locked down the Photos
Library API in March 2025 — `photoslibrary.readonly` and similar scopes
now return 403, and library access is restricted to content your own app
created. The replacement is the Picker API, which requires an interactive
user-facing selection flow, not a programmatic search — it doesn't fit a
headless tool call in the bounded agent loop. Revisit if/when Google
ships something closer to the old behavior, or scope down to "let the
user pick photos via the Picker UI, then operate on that selection."

### Google Cloud setup (one-time, before these tools will authenticate)

1. Go to console.cloud.google.com, create a project (or reuse one).
2. APIs & Services -> Library -> enable: Google Calendar API, Google
   Drive API, Gmail API, Google Sheets API.
3. APIs & Services -> OAuth consent screen -> set it up in Testing mode,
   add your own Google account as a test user.
4. APIs & Services -> Credentials -> Create Credentials -> OAuth client
   ID -> Application type: Desktop app.
5. Download the JSON, rename it `credentials.json`, place it next to
   `Main.py` (already gitignored — never commit this).
6. Turn on the tools you want in `config.json`'s `ToolFlags`
   (`CalendarLookup`, `CalendarCreateEvent`, `DriveSearch`,
   `SheetsAccess`, `GmailAccess`).
7. First run with any of those enabled opens a browser for you to sign
   in and consent — after that, the token's cached (encrypted) so you
   won't be prompted again until it expires.

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

## Editing behavior

The assistant's instructions/persona live in `config.json` under
`"SystemPrompt"` — edit that string to change tone, add standing
instructions ("always answer in one paragraph", "call me by my first
name", etc.), or narrow what it should/shouldn't do. It's plain text, no
code changes needed. If `config.json` doesn't exist yet, copy the
`SystemPrompt` key out of `Config.py`'s `DefaultConfig` to create one.

Other behavior knobs, also in `config.json`:
- `"MaxToolCallsPerRequest"` — the bounded-loop cap (default 5)
- `"ToolFlags"` — enable/disable individual tools
- `"ScopedDirectories"` — what FileSearch/FileManager can touch


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
2. Write actions: CalendarCreateEvent, FileManager, confirmation + logging pattern — done
3. Google Workspace: DriveSearch, SheetsAccess, GmailAccess, PhotosSearch, GoogleXFileDedup, unified search — **current** (PhotosSearch blocked by Google's 2025 API changes; unified search still to build)
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
