from googleapiclient.discovery import build
from Tools.BaseTool import BaseTool, ToolResult


class SheetsAccess(BaseTool):
    Name = "SheetsAccess"
    Description = "Read or write a specific range in a Google Sheet."
    IsDestructive = True  # 'Write' modifies real data — confirm before writing

    def __init__(self, CredentialsObject):
        self.Service = build("sheets", "v4", credentials=CredentialsObject)

    def GetSchema(self):
        return {
            "name": self.Name,
            "description": self.Description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "Action": {"type": "string", "enum": ["Read", "Write"]},
                    "SpreadsheetId": {"type": "string", "description": "The Google Sheet's ID from its URL"},
                    "Range": {"type": "string", "description": "A1 notation range, e.g. 'Sheet1!A1:C10'"},
                    "Values": {
                        "type": "array",
                        "description": "2D array of rows for Write. Not used for Read.",
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "required": ["Action", "SpreadsheetId", "Range"],
            },
        }

    def Execute(self, Action, SpreadsheetId, Range, Values=None):
        try:
            if Action == "Read":
                Result = (
                    self.Service.spreadsheets()
                    .values()
                    .get(spreadsheetId=SpreadsheetId, range=Range)
                    .execute()
                )
                return ToolResult(Success=True, Data=Result.get("values", []))

            if Action == "Write":
                if not Values:
                    return ToolResult(Success=False, Error="Values is required for Write.")
                Body = {"values": Values}
                Result = (
                    self.Service.spreadsheets()
                    .values()
                    .update(
                        spreadsheetId=SpreadsheetId,
                        range=Range,
                        valueInputOption="USER_ENTERED",
                        body=Body,
                    )
                    .execute()
                )
                return ToolResult(Success=True, Data={"UpdatedCells": Result.get("updatedCells")})

            return ToolResult(Success=False, Error=f"Unknown action: {Action}")
        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))
