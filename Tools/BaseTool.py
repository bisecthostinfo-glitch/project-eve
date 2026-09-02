class ToolResult:
    def __init__(self, Success, Data=None, Error=None, NeedsConfirmation=False, ConfirmationPrompt=None):
        self.Success = Success
        self.Data = Data
        self.Error = Error
        self.NeedsConfirmation = NeedsConfirmation
        self.ConfirmationPrompt = ConfirmationPrompt

    def ToDict(self):
        return {
            "Success": self.Success,
            "Data": self.Data,
            "Error": self.Error,
            "NeedsConfirmation": self.NeedsConfirmation,
            "ConfirmationPrompt": self.ConfirmationPrompt,
        }


class BaseTool:
    Name = "BaseTool"
    Description = "Override me"
    IsDestructive = False

    def GetSchema(self):
        raise NotImplementedError

    def Execute(self, **Arguments):
        raise NotImplementedError


def RequestConfirmation(Prompt):
    Answer = input(f"[CONFIRM] {Prompt} (yes/no): ").strip().lower()
    return Answer in ("y", "yes")
