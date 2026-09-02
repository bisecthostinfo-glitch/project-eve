class BaseProvider:
    def CreateMessage(self, SystemPrompt, Messages, ToolSchemas):
        """
        Messages: list of {"role": "user"|"assistant", "content": [Block, ...]}
        Block types (normalized, provider-agnostic):
          {"type": "text", "text": str}
          {"type": "tool_use", "id": str, "name": str, "input": dict}
          {"type": "tool_result", "tool_use_id": str, "content": str, "is_error": bool}

        Returns: list of normalized Blocks representing the assistant's reply.
        """
        raise NotImplementedError
