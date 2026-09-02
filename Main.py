import os
from Config import LoadConfig
from Logger import ActionLogger
from AgentLoop import AgentLoop
from Tools.CalendarLookup import CalendarLookup
from Tools.FileSearch import FileSearch
from Providers.AnthropicProvider import AnthropicProvider
from Providers.OllamaProvider import OllamaProvider


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

    if ConfigDict["ToolFlags"].get("CalendarLookup"):
        Registry["CalendarLookup"] = CalendarLookup()

    if ConfigDict["ToolFlags"].get("FileSearch"):
        SearchTool = FileSearch(ConfigDict["FileIndexPath"], ConfigDict["ScopedDirectories"])
        Registry["FileSearch"] = SearchTool

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
