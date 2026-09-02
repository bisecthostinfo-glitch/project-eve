import os
import json

DefaultConfig = {
    "ScopedDirectories": [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
    ],
    "ToolFlags": {
        "CalendarLookup": True,
        "CalendarCreateEvent": False,
        "FileSearch": True,
        "FileManager": False,
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
    "FileIndexPath": os.path.join(os.path.dirname(__file__), "Data", "FileIndex.db"),
    "ActionLogPath": os.path.join(os.path.dirname(__file__), "Data", "ActionLog.jsonl"),
    "LlmProvider": "anthropic",  # "anthropic" or "ollama"
    "AnthropicModel": "claude-sonnet-4-6",
    "OllamaModel": "qwen2.5:7b",
    "OllamaBaseUrl": "http://localhost:11434/v1",
}

ConfigPath = os.path.join(os.path.dirname(__file__), "config.json")


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
