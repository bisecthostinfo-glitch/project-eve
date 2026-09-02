import json
import os
import time


class ActionLogger:
    def __init__(self, LogPath):
        self.LogPath = LogPath
        os.makedirs(os.path.dirname(LogPath), exist_ok=True)

    def LogAction(self, ToolName, Arguments, Result=None, Status="ok"):
        Entry = {
            "Timestamp": time.time(),
            "Tool": ToolName,
            "Arguments": Arguments,
            "Result": Result,
            "Status": Status,
        }
        with open(self.LogPath, "a") as LogFile:
            LogFile.write(json.dumps(Entry) + "\n")
        return Entry

    def GetLastAction(self):
        if not os.path.exists(self.LogPath):
            return None
        with open(self.LogPath, "r") as LogFile:
            Lines = LogFile.readlines()
        if not Lines:
            return None
        return json.loads(Lines[-1])
