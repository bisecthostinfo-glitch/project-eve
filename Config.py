import os
import sys
import json

if getattr(sys, "frozen", False):
    AppDir = os.path.dirname(sys.executable)
else:
    AppDir = os.path.dirname(__file__)

DefaultConfig = {
    "ScopedDirectories": [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
    ],
    "ToolFlags": {
        "CalendarLookup": True,
        "CalendarCreateEvent": True,
        "FileSearch": True,
        "FileManager": True,
        "DriveSearch": False,
        "SheetsAccess": False,
        "GmailAccess": False,
        "PhotosSearch": False,
        "SystemControl": False,
        "DownloadManager": False,
        "DiscordSearch": False,
        "AutoWriting": False,
    },
    "MaxToolCallsPerRequest": 5,
    "FileIndexPath": os.path.join(AppDir, "Data", "FileIndex.db"),
    "ActionLogPath": os.path.join(AppDir, "Data", "ActionLog.jsonl"),
    "LlmProvider": "anthropic",  # "anthropic" or "ollama"
    "AnthropicModel": "claude-sonnet-4-6",
    "OllamaModel": "qwen2.5:7b",
    "OllamaBaseUrl": "http://localhost:11434/v1",
    "SystemPrompt": (
        "You are a personal assistant with access to a bounded set of tools. "
        "You may call at most a limited number of tools per user request. "
        "If a tool call fails, stop and report the failure instead of trying "
        "another tool on your own. Be direct and concise."
    ),
    "VoiceEnabled": False,
    "WhisperModelSize": "base.en",
    "PiperVoiceModelPath": os.path.join(AppDir, "Data", "PiperVoices", "en_US-lessac-medium.onnx"),
    "PiperVoiceConfigPath": None,
}

ConfigPath = os.path.join(AppDir, "config.json")


def LoadConfig():
    if os.path.exists(ConfigPath):
        with open(ConfigPath, "r") as ConfigFile:
            UserConfig = json.load(ConfigFile)
        Merged = dict(DefaultConfig)
        Merged.update(UserConfig)
        return Merged
    return DefaultConfig


def SaveConfig(ConfigDict):
    with open(ConfigPath, "w") as ConfigFile:
        json.dump(ConfigDict, ConfigFile, indent=2)
