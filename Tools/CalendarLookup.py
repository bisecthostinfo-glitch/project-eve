from Tools.BaseTool import BaseTool, ToolResult


class CalendarLookup(BaseTool):
    Name = "CalendarLookup"
    Description = "Look up events on the user's Google Calendar within a date range."
    IsDestructive = False

    def __init__(self, CalendarService=None):
        # CalendarService should be an authenticated googleapiclient Resource.
        # Left as None until OAuth flow is wired up in Milestone 3.
        self.CalendarService = CalendarService

    def GetSchema(self):
        return {
            "name": self.Name,
            "description": self.Description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "StartDate": {"type": "string", "description": "ISO date, e.g. 2026-09-02"},
                    "EndDate": {"type": "string", "description": "ISO date, e.g. 2026-09-05"},
                    "Query": {"type": "string", "description": "Optional free-text search term"},
                },
                "required": ["StartDate", "EndDate"],
            },
        }
    def Execute(self, StartDate, EndDate, Query=None):
        if self.CalendarService is None:
            return ToolResult(
                Success=False,
                Error="CalendarService not configured. OAuth setup pending (Milestone 3).",
            )

        try:
            TimeMin = f"{StartDate}T00:00:00Z"
            TimeMax = f"{EndDate}T23:59:59Z"
            RequestParams = {
                "calendarId": "primary",
                "timeMin": TimeMin,
                "timeMax": TimeMax,
                "singleEvents": True,
                "orderBy": "startTime",
            }
            if Query:
                RequestParams["q"] = Query

            EventsResult = self.CalendarService.events().list(**RequestParams).execute()
            Items = EventsResult.get("items", [])

            Events = [
                {
                    "Summary": Item.get("summary", "(no title)"),
                    "Start": Item.get("start", {}).get("dateTime", Item.get("start", {}).get("date")),
                    "End": Item.get("end", {}).get("dateTime", Item.get("end", {}).get("date")),
                }
                for Item in Items
            ]
            return ToolResult(Success=True, Data=Events)
        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))
