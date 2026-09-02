import os
from Config import LoadConfig, AppDir
from Logger import ActionLogger
from AgentLoop import AgentLoop
from Tools.CalendarLookup import CalendarLookup
from Tools.CalendarCreateEvent import CalendarCreateEvent
from Tools.FileSearch import FileSearch
from Tools.FileManager import FileManager
from Tools.DriveSearch import DriveSearch
from Tools.SheetsAccess import SheetsAccess
from Tools.GmailAccess import GmailAccess
from Providers.AnthropicProvider import AnthropicProvider
from Providers.OllamaProvider import OllamaProvider
from GoogleAuth import GoogleAuth


def BuildProvider(ConfigDict):
    ProviderName = os.environ.get("LLM_PROVIDER", ConfigDict["LlmProvider"])

    if ProviderName == "ollama":
        Model = os.environ.get("OLLAMA_MODEL", ConfigDict["OllamaModel"])
        BaseUrl = os.environ.get("OLLAMA_BASE_URL", ConfigDict["OllamaBaseUrl"])
        print(f"Using Ollama provider — model: {Model} @ {BaseUrl}")
        return OllamaProvider(Model=Model, BaseUrl=BaseUrl)

    ApiKey = os.environ.get("ANTHROPIC_API_KEY")
    if not ApiKey:
        print("LlmProvider is 'anthropic' but ANTHROPIC_API_KEY is not set.")
        return None
    print(f"Using Anthropic provider — model: {ConfigDict['AnthropicModel']}")
    return AnthropicProvider(ApiKey=ApiKey, Model=ConfigDict["AnthropicModel"])


def BuildToolRegistry(ConfigDict):
    Registry = {}
    Flags = ConfigDict["ToolFlags"]

    GoogleToolsRequested = any(
        Flags.get(Name) for Name in ("CalendarLookup", "CalendarCreateEvent", "DriveSearch", "SheetsAccess", "GmailAccess")
    )
    GoogleCredentials = None
    if GoogleToolsRequested:
        try:
            GoogleCredentials = GoogleAuth(AppDir).GetCredentials()
        except FileNotFoundError as ErrorObject:
            print(f"Google tools disabled: {ErrorObject}")

    if Flags.get("CalendarLookup"):
        Registry["CalendarLookup"] = CalendarLookup(CalendarService=None)
        if GoogleCredentials:
            from googleapiclient.discovery import build
            Registry["CalendarLookup"].CalendarService = build("calendar", "v3", credentials=GoogleCredentials)

    if Flags.get("CalendarCreateEvent"):
        Registry["CalendarCreateEvent"] = CalendarCreateEvent(CalendarService=None)
        if GoogleCredentials:
            from googleapiclient.discovery import build
            Registry["CalendarCreateEvent"].CalendarService = build("calendar", "v3", credentials=GoogleCredentials)

    if Flags.get("FileSearch"):
        SearchTool = FileSearch(ConfigDict["FileIndexPath"], ConfigDict["ScopedDirectories"])
        Registry["FileSearch"] = SearchTool

    if Flags.get("FileManager"):
        Registry["FileManager"] = FileManager(ConfigDict["ScopedDirectories"])

    if Flags.get("DriveSearch") and GoogleCredentials:
        Registry["DriveSearch"] = DriveSearch(GoogleCredentials, FileIndexPath=ConfigDict["FileIndexPath"])

    if Flags.get("SheetsAccess") and GoogleCredentials:
        Registry["SheetsAccess"] = SheetsAccess(GoogleCredentials)

    if Flags.get("GmailAccess") and GoogleCredentials:
        Registry["GmailAccess"] = GmailAccess(GoogleCredentials)

    return Registry


def Main():
    ConfigDict = LoadConfig()
    Provider = BuildProvider(ConfigDict)
    if Provider is None:
        return

    ToolRegistry = BuildToolRegistry(ConfigDict)
    ActionLoggerInstance = ActionLogger(ConfigDict["ActionLogPath"])

    if "FileSearch" in ToolRegistry:
        print("Building FileIndex from scoped directories...")
        ToolRegistry["FileSearch"].RebuildIndex()

    Loop = AgentLoop(
        Provider=Provider,
        ToolRegistry=ToolRegistry,
        ActionLogger=ActionLoggerInstance,
        MaxToolCalls=ConfigDict["MaxToolCallsPerRequest"],
        SystemPrompt=ConfigDict["SystemPrompt"],
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

        try:
            Result = Loop.HandleRequest(UserInput, ConversationHistory)
        except Exception as ErrorObject:
            print(f"Assistant: Something went wrong talking to the model — {ErrorObject}")
            continue

        ConversationHistory = Result["Messages"]
        print(f"Assistant: {Result['FinalResponse'] or '(no response text — check StepLog / logs)'}")


if __name__ == "__main__":
    Main()
