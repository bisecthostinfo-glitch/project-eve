import os
import sqlite3
from Tools.BaseTool import BaseTool, ToolResult


class FileSearch(BaseTool):
    Name = "FileSearch"
    Description = "Search the local FileIndex for files by name or content within scoped directories."
    IsDestructive = False

    def __init__(self, IndexPath, ScopedDirectories):
        self.IndexPath = IndexPath
        self.ScopedDirectories = ScopedDirectories
        self.EnsureIndex()

    def GetConnection(self):
        os.makedirs(os.path.dirname(self.IndexPath), exist_ok=True)
        return sqlite3.connect(self.IndexPath)

    def EnsureIndex(self):
        Connection = self.GetConnection()
        Cursor = Connection.cursor()
        Cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS FileIndex
            USING fts5(FileName, FilePath, Content, ModifiedTime UNINDEXED)
            """
        )
        Connection.commit()
        Connection.close()

    def RebuildIndex(self):
        Connection = self.GetConnection()
        Cursor = Connection.cursor()
        Cursor.execute("DELETE FROM FileIndex")

        for Directory in self.ScopedDirectories:
            if not os.path.isdir(Directory):
                continue
            for Root, _Dirs, Files in os.walk(Directory):
                for FileName in Files:
                    FullPath = os.path.join(Root, FileName)
                    try:
                        ModifiedTime = os.path.getmtime(FullPath)
                    except OSError:
                        continue
                    Content = ""
                    if FileName.lower().endswith(
                        (".txt", ".md", ".py", ".json", ".csv", ".log", ".yaml", ".yml", ".ini", ".xml")
                    ):
                        try:
                            with open(FullPath, "r", errors="ignore") as OpenFile:
                                Content = OpenFile.read()[:20000]
                        except OSError:
                            pass
                    Cursor.execute(
                        "INSERT INTO FileIndex (FileName, FilePath, Content, ModifiedTime) VALUES (?, ?, ?, ?)",
                        (FileName, FullPath, Content, ModifiedTime),
                    )
        Connection.commit()
        Connection.close()

    def GetSchema(self):
        return {
            "name": self.Name,
            "description": self.Description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "Query": {"type": "string", "description": "Search term for filename or file content"},
                    "MaxResults": {"type": "integer", "description": "Maximum number of results to return"},
                },
                "required": ["Query"],
            },
        }

    def Execute(self, Query, MaxResults=10):
        try:
            Connection = self.GetConnection()
            Cursor = Connection.cursor()
            Cursor.execute(
                "SELECT FileName, FilePath, ModifiedTime FROM FileIndex WHERE FileIndex MATCH ? LIMIT ?",
                (Query, MaxResults),
            )
            Rows = Cursor.fetchall()
            Connection.close()
            Results = [
                {"FileName": Row[0], "FilePath": Row[1], "ModifiedTime": Row[2]} for Row in Rows
            ]
            return ToolResult(Success=True, Data=Results)
        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))
