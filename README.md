# Personal AI Assistant

Voice-capable personal assistant with LLM tool-calling access to Calendar,
Google Workspace, local files, email, Discord, and OS/app control.

Guardrails are minimal by design: no content filtering, but confirmation is
required before delete, send, purchase, download, or any irreversible
action. Every tool call is logged.

## Status: Milestone 1 — text prototype + bounded loop

Implemented:
- `AgentLoop.py` — bounded agentic loop, hard cap of 5 tool calls per
  request, stops and reports on tool failure instead of retrying with a
  different tool, logs every step, confirmation checkpoints for
  destructive tools fire mid-chain.
- `Tools/CalendarLookup.py` — Google Calendar read (OAuth wiring pending,
  Milestone 3).
- `Tools/FileSearch.py` — local SQLite FTS index over scoped directories.
- `Config.py` — central config: scoped directories, per-tool enable
  flags, tool-call cap.
- `Logger.py` — JSONL action log, powers "what did you just do".

Not yet built (see roadmap below): write actions, Google Workspace beyond
Calendar, SystemControl, DownloadManager, AutoWriting, Discord, persistent
memory, voice I/O, wake word + speaker ID, reliability pass.

## Setup

```
pip install -r requirements.txt
cp .env.example .env   # fill in your own key, then export it
export ANTHROPIC_API_KEY=...
python Main.py
```

`config.json` (gitignored) overrides `Config.DefaultConfig` — copy the
`ScopedDirectories` / `ToolFlags` shape from `Config.py` if you want to
customize before Milestone 3 adds a proper setup flow.

## Roadmap

1. Text prototype + bounded loop — **current**
2. Write actions: CalendarCreateEvent, FileManager, confirmation + logging pattern
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
