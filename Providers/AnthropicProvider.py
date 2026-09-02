import anthropic
from Providers.BaseProvider import BaseProvider


class AnthropicProvider(BaseProvider):
    def __init__(self, ApiKey, Model):
        self.Client = anthropic.Anthropic(api_key=ApiKey)
        self.Model = Model

    def CreateMessage(self, SystemPrompt, Messages, ToolSchemas):
        WireMessages = []
        for Message in Messages:
            WireContent = []
            for Block in Message["content"]:
                if Block["type"] == "text":
                    WireContent.append({"type": "text", "text": Block["text"]})
                elif Block["type"] == "tool_use":
                    WireContent.append(
                        {
                            "type": "tool_use",
                            "id": Block["id"],
                            "name": Block["name"],
                            "input": Block["input"],
                        }
                    )
                elif Block["type"] == "tool_result":
                    WireContent.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": Block["tool_use_id"],
                            "content": Block["content"],
                            "is_error": Block.get("is_error", False),
                        }
                    )
            WireMessages.append({"role": Message["role"], "content": WireContent})

        Response = self.Client.messages.create(
            model=self.Model,
            max_tokens=1024,
            system=SystemPrompt,
            tools=ToolSchemas,
            messages=WireMessages,
        )

        NormalizedBlocks = []
        for Block in Response.content:
            if Block.type == "text":
                NormalizedBlocks.append({"type": "text", "text": Block.text})
            elif Block.type == "tool_use":
                NormalizedBlocks.append(
                    {"type": "tool_use", "id": Block.id, "name": Block.name, "input": Block.input}
                )
        return NormalizedBlocks
