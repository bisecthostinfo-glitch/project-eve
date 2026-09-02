import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from Tools.BaseTool import BaseTool, ToolResult


class GmailAccess(BaseTool):
    Name = "GmailAccess"
    Description = "Search, read, draft, or send Gmail messages. Sending requires confirmation."
    IsDestructive = True  # loop confirms before ANY call; Search/Read/Draft are
    # actually safe, but gating the whole tool keeps the confirmation logic
    # simple and matches the project's "minimal but present" guardrail rule —
    # split into a separate low-risk tool later if the extra prompts get annoying.

    def __init__(self, CredentialsObject):
        self.Service = build("gmail", "v1", credentials=CredentialsObject)

    def GetSchema(self):
        return {
            "name": self.Name,
            "description": self.Description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "Action": {"type": "string", "enum": ["Search", "Read", "Draft", "Send"]},
                    "Query": {"type": "string", "description": "Gmail search query, for Search"},
                    "MessageId": {"type": "string", "description": "Gmail message id, for Read"},
                    "To": {"type": "string", "description": "Recipient email, for Draft/Send"},
                    "Subject": {"type": "string", "description": "Email subject, for Draft/Send"},
                    "Body": {"type": "string", "description": "Email body text, for Draft/Send"},
                    "MaxResults": {"type": "integer", "description": "Max results for Search"},
                },
                "required": ["Action"],
            },
        }

    def Execute(self, Action, Query=None, MessageId=None, To=None, Subject=None, Body=None, MaxResults=10):
        try:
            if Action == "Search":
                Response = (
                    self.Service.users()
                    .messages()
                    .list(userId="me", q=Query or "", maxResults=MaxResults)
                    .execute()
                )
                Messages = Response.get("messages", [])
                return ToolResult(Success=True, Data=Messages)

            if Action == "Read":
                if not MessageId:
                    return ToolResult(Success=False, Error="MessageId is required for Read.")
                MessageData = (
                    self.Service.users()
                    .messages()
                    .get(userId="me", id=MessageId, format="full")
                    .execute()
                )
                Headers = {
                    Header["name"]: Header["value"]
                    for Header in MessageData.get("payload", {}).get("headers", [])
                }
                return ToolResult(
                    Success=True,
                    Data={
                        "From": Headers.get("From"),
                        "Subject": Headers.get("Subject"),
                        "Snippet": MessageData.get("snippet"),
                    },
                )

            if Action in ("Draft", "Send"):
                if not (To and Subject and Body):
                    return ToolResult(Success=False, Error="To, Subject, and Body are required.")
                MimeMessage = MIMEText(Body)
                MimeMessage["to"] = To
                MimeMessage["subject"] = Subject
                RawMessage = base64.urlsafe_b64encode(MimeMessage.as_bytes()).decode()

                if Action == "Draft":
                    Result = (
                        self.Service.users()
                        .drafts()
                        .create(userId="me", body={"message": {"raw": RawMessage}})
                        .execute()
                    )
                    return ToolResult(Success=True, Data={"DraftId": Result.get("id")})

                Result = (
                    self.Service.users()
                    .messages()
                    .send(userId="me", body={"raw": RawMessage})
                    .execute()
                )
                return ToolResult(Success=True, Data={"MessageId": Result.get("id")})

            return ToolResult(Success=False, Error=f"Unknown action: {Action}")
        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))
