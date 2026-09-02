import os
from Config import LoadConfig
from Logger import ActionLogger
from AgentLoop import AgentLoop
from Tools.CalendarLookup import CalendarLookup
from Tools.FileSearch import FileSearch


def BuildToolRegistry(ConfigDict):
    Registry = {}

    if ConfigDict["ToolFlags"].get("CalendarLookup"):
        Registry["CalendarLookup"] = CalendarLookup()

    if ConfigDict["ToolFlags"].get("FileSearch"):
        SearchTool = FileSearch(ConfigDict["FileIndexPath"], ConfigDict["ScopedDirectories"])
        Registry["FileSearch"] = SearchTool

    return Registry


def Main():
    ConfigDict = LoadConfig()
    ApiKey = os.environ.get("ANTHROPIC_API_KEY")
    if not ApiKey:
        print("Set the ANTHROPIC_API_KEY environment variable before running.")
        return

    ToolRegistry = BuildToolRegistry(ConfigDict)
    ActionLoggerInstance = ActionLogger(ConfigDict["ActionLogPath"])

    if "FileSearch" in ToolRegistry:
        print("Building FileIndex from scoped directories...")
        ToolRegistry["FileSearch"].RebuildIndex()

    Loop = AgentLoop(
        ApiKey=ApiKey,
        Model=ConfigDict["AnthropicModel"],
        ToolRegistry=ToolRegistry,
        ActionLogger=ActionLoggerInstance,
        MaxToolCalls=ConfigDict["MaxToolCallsPerRequest"],
    )

    print("Personal Assistant (Milestone 1 — text mode). Type 'exit' to quit.")
    ConversationHistory = []

    while True:
        UserInput = input("\nYou: ").strip()
        if UserInput.lower() in ("exit", "quit"):
            break
        if UserInput.lower() == "what did you just do":
            LastAction = ActionLoggerInstance.GetLastAction()
            print(f"Assistant: {LastAction}")
            continue

        Result = Loop.HandleRequest(UserInput, ConversationHistory)
        ConversationHistory = Result["Messages"]
        print(f"Assistant: {Result['FinalResponse']}")


if __name__ == "__main__":
    Main()
