from googleapiclient.discovery import build
from Tools.BaseTool import BaseTool, ToolResult
from GoogleXFileDedup import FilterDriveResultsAgainstLocal


class DriveSearch(BaseTool):
    Name = "DriveSearch"
    Description = (
        "Search the user's Google Drive for files or folders by name/content. "
        "Results exclude files that already exist locally (see FileSearch)."
    )
    IsDestructive = False

    def __init__(self, CredentialsObject, FileIndexPath=None):
        self.Service = build("drive", "v3", credentials=CredentialsObject)
        self.FileIndexPath = FileIndexPath

    def GetSchema(self):
        return {
            "name": self.Name,
            "description": self.Description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "Query": {"type": "string", "description": "Search term (matches name and content)"},
                    "MaxResults": {"type": "integer", "description": "Maximum number of results"},
                },
                "required": ["Query"],
            },
        }

    def Execute(self, Query, MaxResults=10):
        try:
            EscapedQuery = Query.replace("'", "\\'")
            DriveQuery = f"fullText contains '{EscapedQuery}' or name contains '{EscapedQuery}'"
            Response = (
                self.Service.files()
                .list(
                    q=DriveQuery,
                    pageSize=MaxResults,
                    fields="files(id, name, mimeType, webViewLink, modifiedTime, owners)",
                )
                .execute()
            )
            Files = [
                {
                    "Id": FileEntry.get("id"),
                    "Name": FileEntry.get("name"),
                    "MimeType": FileEntry.get("mimeType"),
                    "WebViewLink": FileEntry.get("webViewLink"),
                    "ModifiedTime": FileEntry.get("modifiedTime"),
                }
                for FileEntry in Response.get("files", [])
            ]
            if self.FileIndexPath:
                Files = FilterDriveResultsAgainstLocal(Files, self.FileIndexPath)
            return ToolResult(Success=True, Data=Files)
        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))
