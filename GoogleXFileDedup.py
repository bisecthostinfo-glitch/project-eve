import sqlite3


def FilterDriveResultsAgainstLocal(DriveResults, FileIndexPath):
    """
    Runs after DriveSearch. Drops any Drive file whose name already has a
    local match in FileIndex, so results only surface Drive files the user
    doesn't already have a copy of. Not a separate registered tool —
    called directly from wherever DriveSearch results are consumed.
    """
    try:
        Connection = sqlite3.connect(FileIndexPath)
        Cursor = Connection.cursor()

        Filtered = []
        for DriveFile in DriveResults:
            FileName = DriveFile.get("Name", "")
            Cursor.execute(
                "SELECT 1 FROM FileIndex WHERE FileName = ? LIMIT 1", (FileName,)
            )
            if Cursor.fetchone() is None:
                Filtered.append(DriveFile)

        Connection.close()
        return Filtered
    except sqlite3.Error:
        # FileIndex not built yet or unreadable — fail open, return
        # unfiltered results rather than hiding everything.
        return DriveResults
