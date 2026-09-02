import json
import uuid
from openai import OpenAI
from Providers.BaseProvider import BaseProvider


class OllamaProvider(BaseProvider):
    def __init__(self, Model, BaseUrl="http://localhost:11434/v1"):
        # Ollama's OpenAI-compatible endpoint ignores the api_key but the
        # client requires a non-empty string.
        self.Client = OpenAI(base_url=BaseUrl, api_key="ollama")
        self.Model = Model

    def ToOpenAiTools(self, ToolSchemas):
        OpenAiTools = []
        for Schema in ToolSchemas:
            OpenAiTools.append(
                {
                    "type": "function",
                    "function": {
                        "name": Schema["name"],
                        "description": Schema["description"],
                        "parameters": Schema["input_schema"],
                    },
                }
            )
        return OpenAiTools

    def ToOpenAiMessages(self, SystemPrompt, Messages):
        WireMessages = [{"role": "system", "content": SystemPrompt}]

        for Message in Messages:
            TextParts = [B["text"] for B in Message["content"] if B["type"] == "text"]
            ToolUseBlocks = [B for B in Message["content"] if B["type"] == "tool_use"]
            ToolResultBlocks = [B for B in Message["content"] if B["type"] == "tool_result"]

            if Message["role"] == "assistant" and ToolUseBlocks:
                WireMessages.append(
                    {
                        "role": "assistant",
                        "content": " ".join(TextParts) if TextParts else None,
                        "tool_calls": [
                            {
                                "id": Block["id"],
                                "type": "function",
                                "function": {
                                    "name": Block["name"],
                                    "arguments": json.dumps(Block["input"]),
                                },
                            }
                            for Block in ToolUseBlocks
                        ],
                    }
                )
            elif ToolResultBlocks:
                for Block in ToolResultBlocks:
                    WireMessages.append(
                        {
                            "role": "tool",
                            "tool_call_id": Block["tool_use_id"],
                            "content": Block["content"],
                        }
                    )
            else:
                WireMessages.append({"role": Message["role"], "content": " ".join(TextParts)})

        return WireMessages

    def CreateMessage(self, SystemPrompt, Messages, ToolSchemas):
        WireMessages = self.ToOpenAiMessages(SystemPrompt, Messages)
        OpenAiTools = self.ToOpenAiTools(ToolSchemas)

        Response = self.Client.chat.completions.create(
            model=self.Model,
            messages=WireMessages,
            tools=OpenAiTools if OpenAiTools else None,
        )

        Choice = Response.choices[0].message
        NormalizedBlocks = []

        if Choice.content:
            NormalizedBlocks.append({"type": "text", "text": Choice.content})

        if Choice.tool_calls:
            for ToolCall in Choice.tool_calls:
                try:
                    ParsedArgs = json.loads(ToolCall.function.arguments)
                except json.JSONDecodeError:
                    ParsedArgs = {}
                NormalizedBlocks.append(
                    {
                        "type": "tool_use",
                        "id": ToolCall.id or str(uuid.uuid4()),
                        "name": ToolCall.function.name,
                        "input": ParsedArgs,
                    }
                )

        return NormalizedBlocks
