from Tools.BaseTool import BaseTool, ToolResult


class CalendarCreateEvent(BaseTool):
    Name = "CalendarCreateEvent"
    Description = "Create a new event on the user's Google Calendar."
    IsDestructive = True  # writes to the user's real calendar, confirm first

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
                    "Summary": {"type": "string", "description": "Event title"},
                    "StartDateTime": {
                        "type": "string",
                        "description": "ISO 8601 datetime, e.g. 2026-09-05T14:00:00",
                    },
                    "EndDateTime": {
                        "type": "string",
                        "description": "ISO 8601 datetime, e.g. 2026-09-05T15:00:00",
                    },
                    "Description": {"type": "string", "description": "Optional event details"},
                    "Location": {"type": "string", "description": "Optional event location"},
                    "TimeZone": {"type": "string", "description": "IANA timezone, e.g. Europe/Bratislava"},
                },
                "required": ["Summary", "StartDateTime", "EndDateTime"],
            },
        }

    def Execute(self, Summary, StartDateTime, EndDateTime, Description=None, Location=None, TimeZone="UTC"):
        if self.CalendarService is None:
            return ToolResult(
                Success=False,
                Error="CalendarService not configured. OAuth setup pending (Milestone 3).",
            )

        try:
            EventBody = {
                "summary": Summary,
                "start": {"dateTime": StartDateTime, "timeZone": TimeZone},
                "end": {"dateTime": EndDateTime, "timeZone": TimeZone},
            }
            if Description:
                EventBody["description"] = Description
            if Location:
                EventBody["location"] = Location

            CreatedEvent = (
                self.CalendarService.events()
                .insert(calendarId="primary", body=EventBody)
                .execute()
            )
            return ToolResult(
                Success=True,
                Data={
                    "EventId": CreatedEvent.get("id"),
                    "HtmlLink": CreatedEvent.get("htmlLink"),
                    "Summary": CreatedEvent.get("summary"),
                },
            )
        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))
