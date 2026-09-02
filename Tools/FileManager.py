import os
import shutil
import zipfile
from Tools.BaseTool import BaseTool, ToolResult

try:
    import py7zr
    Has7z = True
except ImportError:
    Has7z = False

try:
    import rarfile
    HasRar = True
except ImportError:
    HasRar = False


class FileManager(BaseTool):
    Name = "FileManager"
    Description = (
        "Move, rename, or delete files within scoped directories, or extract "
        "an archive (.zip, .rar, .7z) into the folder it's in."
    )
    IsDestructive = True  # only 'Delete' truly needs confirmation, but keep
    # the whole tool gated to be safe — cheap insurance against a bad Move
    # clobbering a file the user didn't mean to touch.

    def __init__(self, ScopedDirectories):
        self.ScopedDirectories = [os.path.abspath(Directory) for Directory in ScopedDirectories]

    def IsPathInScope(self, TargetPath):
        AbsTarget = os.path.abspath(TargetPath)
        return any(
            AbsTarget == Scope or AbsTarget.startswith(Scope + os.sep)
            for Scope in self.ScopedDirectories
        )

    def GetSchema(self):
        return {
            "name": self.Name,
            "description": self.Description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "Action": {
                        "type": "string",
                        "enum": ["Move", "Rename", "Delete", "Extract"],
                        "description": "Which file operation to perform",
                    },
                    "SourcePath": {"type": "string", "description": "Full path to the target file"},
                    "DestinationPath": {
                        "type": "string",
                        "description": "Full path for Move/Rename destination. Not used for Delete/Extract.",
                    },
                },
                "required": ["Action", "SourcePath"],
            },
        }

    def Execute(self, Action, SourcePath, DestinationPath=None):
        if not self.IsPathInScope(SourcePath):
            return ToolResult(Success=False, Error=f"'{SourcePath}' is outside scoped directories.")

        if not os.path.exists(SourcePath):
            return ToolResult(Success=False, Error=f"'{SourcePath}' does not exist.")

        try:
            if Action == "Delete":
                if os.path.isdir(SourcePath):
                    shutil.rmtree(SourcePath)
                else:
                    os.remove(SourcePath)
                return ToolResult(Success=True, Data={"Deleted": SourcePath})

            if Action in ("Move", "Rename"):
                if not DestinationPath:
                    return ToolResult(Success=False, Error="DestinationPath is required for Move/Rename.")
                if not self.IsPathInScope(DestinationPath):
                    return ToolResult(
                        Success=False, Error=f"Destination '{DestinationPath}' is outside scoped directories."
                    )
                shutil.move(SourcePath, DestinationPath)
                return ToolResult(Success=True, Data={"From": SourcePath, "To": DestinationPath})

            if Action == "Extract":
                return self.ExtractArchive(SourcePath)

            return ToolResult(Success=False, Error=f"Unknown action: {Action}")

        except Exception as ErrorObject:
            return ToolResult(Success=False, Error=str(ErrorObject))

    def ExtractArchive(self, SourcePath):
        DestinationDir = os.path.join(
            os.path.dirname(SourcePath), os.path.splitext(os.path.basename(SourcePath))[0]
        )
        os.makedirs(DestinationDir, exist_ok=True)
        LowerPath = SourcePath.lower()

        if LowerPath.endswith(".zip"):
            with zipfile.ZipFile(SourcePath, "r") as ZipRef:
                ZipRef.extractall(DestinationDir)
        elif LowerPath.endswith(".7z"):
            if not Has7z:
                return ToolResult(Success=False, Error="py7zr not installed. Run: pip install py7zr")
            with py7zr.SevenZipFile(SourcePath, "r") as SevenZipRef:
                SevenZipRef.extractall(DestinationDir)
        elif LowerPath.endswith(".rar"):
            if not HasRar:
                return ToolResult(
                    Success=False,
                    Error="rarfile not installed, or unrar.exe missing. "
                    "Run: pip install rarfile, and install unrar/UnRAR.exe on PATH.",
                )
            with rarfile.RarFile(SourcePath, "r") as RarRef:
                RarRef.extractall(DestinationDir)
        else:
            return ToolResult(Success=False, Error="Unsupported archive type. Use .zip, .rar, or .7z.")

        return ToolResult(Success=True, Data={"ExtractedTo": DestinationDir})
