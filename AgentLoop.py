from Tools.BaseTool import RequestConfirmation


class AgentLoop:
    def __init__(self, Provider, ToolRegistry, ActionLogger, MaxToolCalls=5, SystemPrompt=None):
        self.Provider = Provider
        self.ToolRegistry = ToolRegistry  # dict: ToolName -> ToolInstance
        self.ActionLogger = ActionLogger
        self.MaxToolCalls = MaxToolCalls
        self.SystemPrompt = SystemPrompt or (
            "You are a personal assistant with access to a bounded set of tools. "
            "You may call at most a limited number of tools per user request. "
            "If a tool call fails, stop and report the failure instead of trying "
            "another tool on your own. Be direct and concise."
        )

    def GetToolSchemas(self):
        return [Tool.GetSchema() for Tool in self.ToolRegistry.values()]

    def RunTool(self, ToolName, ToolArguments):
        Tool = self.ToolRegistry.get(ToolName)
        if Tool is None:
            return {"Success": False, "Error": f"Unknown tool: {ToolName}"}

        if Tool.IsDestructive:
            Prompt = f"About to run destructive action '{ToolName}' with args {ToolArguments}."
            if not RequestConfirmation(Prompt):
                Result = {"Success": False, "Error": "User declined confirmation."}
                self.ActionLogger.LogAction(ToolName, ToolArguments, Result, Status="declined")
                return Result

        ToolResultObject = Tool.Execute(**ToolArguments)
        ResultDict = ToolResultObject.ToDict()
        Status = "ok" if ToolResultObject.Success else "failed"
        self.ActionLogger.LogAction(ToolName, ToolArguments, ResultDict, Status=Status)
        return ResultDict

    def HandleRequest(self, UserMessage, ConversationHistory=None):
        Messages = list(ConversationHistory) if ConversationHistory else []
        Messages.append({"role": "user", "content": [{"type": "text", "text": UserMessage}]})

        ToolCallCount = 0
        StepLog = []

        while True:
            ToolSchemas = self.GetToolSchemas()
            ResponseBlocks = self.Provider.CreateMessage(self.SystemPrompt, Messages, ToolSchemas)
            Messages.append({"role": "assistant", "content": ResponseBlocks})

            ToolUseBlocks = [Block for Block in ResponseBlocks if Block["type"] == "tool_use"]

            if not ToolUseBlocks:
                FinalText = "".join(
                    Block["text"] for Block in ResponseBlocks if Block["type"] == "text"
                )
                return {"FinalResponse": FinalText, "StepLog": StepLog, "Messages": Messages}

            if ToolCallCount >= self.MaxToolCalls:
                return {
                    "FinalResponse": (
                        "Hit the tool-call cap for this request "
                        f"({self.MaxToolCalls}). Here is what I gathered so far."
                    ),
                    "StepLog": StepLog,
                    "Messages": Messages,
                }

            ToolResultBlocks = []
            StopDueToFailure = False

            for Block in ToolUseBlocks:
                if ToolCallCount >= self.MaxToolCalls:
                    break
                ToolCallCount += 1
                ResultDict = self.RunTool(Block["name"], Block["input"])
                StepLog.append({"Tool": Block["name"], "Arguments": Block["input"], "Result": ResultDict})

                ToolResultBlocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": Block["id"],
                        "content": str(ResultDict),
                        "is_error": not ResultDict.get("Success", False),
                    }
                )

                if not ResultDict.get("Success", False):
                    StopDueToFailure = True

            Messages.append({"role": "user", "content": ToolResultBlocks})

            if StopDueToFailure:
                FailureSystemPrompt = (
                    self.SystemPrompt
                    + " A tool call just failed. Report the failure plainly, do not retry."
                )
                ResponseBlocks = self.Provider.CreateMessage(FailureSystemPrompt, Messages, ToolSchemas)
                Messages.append({"role": "assistant", "content": ResponseBlocks})
                FinalText = "".join(
                    Block["text"] for Block in ResponseBlocks if Block["type"] == "text"
                )
                return {"FinalResponse": FinalText, "StepLog": StepLog, "Messages": Messages}
