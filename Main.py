import os
from Config import LoadConfig, AppDir
from Logger import ActionLogger
from AgentLoop import AgentLoop
from Tools.CalendarLookup import CalendarLookup
from Tools.CalendarCreateEvent import CalendarCreateEvent
from Tools.FileSearch import FileSearch
from Tools.FileManager import FileManager
from Providers.AnthropicProvider import AnthropicProvider
from Providers.OllamaProvider import OllamaProvider
from SecretsStore import SecretsStore


def BuildProvider(ConfigDict):
    ProviderName = os.environ.get("LLM_PROVIDER", ConfigDict["LlmProvider"])

    if ProviderName == "ollama":
        Model = os.environ.get("OLLAMA_MODEL", ConfigDict["OllamaModel"])
        BaseUrl = os.environ.get("OLLAMA_BASE_URL", ConfigDict["OllamaBaseUrl"])
        print(f"Using Ollama provider — model: {Model} @ {BaseUrl}")
        return OllamaProvider(Model=Model, BaseUrl=BaseUrl)

    ApiKey = os.environ.get("ANTHROPIC_API_KEY") or SecretsStore(AppDir).Get("ANTHROPIC_API_KEY")
    if not ApiKey:
        print("LlmProvider is 'anthropic' but no API key is set (env var or SecretsStore).")
        return None
    print(f"Using Anthropic provider — model: {ConfigDict['AnthropicModel']}")
    return AnthropicProvider(ApiKey=ApiKey, Model=ConfigDict["AnthropicModel"])


def BuildToolRegistry(ConfigDict):
    Registry = {}

    if ConfigDict["ToolFlags"].get("CalendarLookup"):
        Registry["CalendarLookup"] = CalendarLookup()

    if ConfigDict["ToolFlags"].get("CalendarCreateEvent"):
        Registry["CalendarCreateEvent"] = CalendarCreateEvent()

    if ConfigDict["ToolFlags"].get("FileSearch"):
        SearchTool = FileSearch(ConfigDict["FileIndexPath"], ConfigDict["ScopedDirectories"])
        Registry["FileSearch"] = SearchTool

    if ConfigDict["ToolFlags"].get("FileManager"):
        Registry["FileManager"] = FileManager(ConfigDict["ScopedDirectories"])

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
