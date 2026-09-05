import tkinter as tk

BackgroundColor = "#0f1117"
LineColor = "#2a2e3a"
NodeColor = "#2d3348"
AiColor = "#4b6bfb"
YouColor = "#3f4658"
HighlightColor = "#22c55e"
TextColor = "#e5e7eb"


class NetworkMap:
    def __init__(self, Parent, ToolNames, Width=220, Height=420):
        self.Width = Width
        self.Height = Height
        self.Canvas = tk.Canvas(Parent, width=Width, height=Height, bg=BackgroundColor, highlightthickness=0)
        self.Canvas.pack(fill="both", expand=True)

        self.Nodes = {}  # Name -> (OvalId, TextId, BaseColor)
        self.Lines = {}  # Name -> LineId (edge from that node to AI)

        self.DrawGraph(ToolNames)

    def DrawGraph(self, ToolNames):
        CenterX = self.Width // 2
        AiY = 70

        YouY = 20
        self.DrawNode("You", CenterX, YouY, YouColor, Radius=22)

        self.DrawNode("AI", CenterX, AiY, AiColor, Radius=30)
        self.DrawEdge("You", CenterX, YouY, CenterX, AiY)

        ToolCount = max(len(ToolNames), 1)
        StartY = 150
        AvailableHeight = self.Height - StartY - 30
        Spacing = AvailableHeight / ToolCount if ToolCount else 0

        for Index, ToolName in enumerate(ToolNames):
            NodeY = StartY + Index * Spacing
            self.DrawEdge(ToolName, CenterX, NodeY, CenterX, AiY, DeferNode=True)
            self.DrawNode(ToolName, CenterX, NodeY, NodeColor, Radius=24)

    def DrawNode(self, Name, X, Y, Color, Radius):
        OvalId = self.Canvas.create_oval(X - Radius, Y - Radius, X + Radius, Y + Radius, fill=Color, outline="")
        TextId = self.Canvas.create_text(
            X, Y, text=Name, fill=TextColor, font=("Segoe UI", 8, "bold"), width=Radius * 2 - 6
        )
        self.Nodes[Name] = (OvalId, TextId, Color)

    def DrawEdge(self, FromName, X1, Y1, X2, Y2, DeferNode=False):
        LineId = self.Canvas.create_line(X1, Y1, X2, Y2, fill=LineColor, width=2)
        self.Lines[FromName] = LineId

    def Activate(self, ToolName):
        if ToolName not in self.Nodes:
            return

        OvalId, _TextId, _BaseColor = self.Nodes[ToolName]
        self.Canvas.itemconfig(OvalId, fill=HighlightColor)

        LineId = self.Lines.get(ToolName)
        if LineId:
            self.Canvas.itemconfig(LineId, fill=HighlightColor, width=3)

        AiOvalId, _AiText, AiBaseColor = self.Nodes["AI"]
        self.Canvas.itemconfig(AiOvalId, fill=HighlightColor)

        self.Canvas.after(900, self.Deactivate, ToolName, AiBaseColor)

    def Deactivate(self, ToolName, AiBaseColor):
        OvalId, _TextId, BaseColor = self.Nodes[ToolName]
        self.Canvas.itemconfig(OvalId, fill=BaseColor)

        LineId = self.Lines.get(ToolName)
        if LineId:
            self.Canvas.itemconfig(LineId, fill=LineColor, width=2)

        AiOvalId, _AiText, _OldColor = self.Nodes["AI"]
        self.Canvas.itemconfig(AiOvalId, fill=AiBaseColor)

    def PulseThinking(self):
        AiOvalId, _AiText, AiBaseColor = self.Nodes["AI"]
        self.Canvas.itemconfig(AiOvalId, fill=HighlightColor)
        self.Canvas.after(400, lambda: self.Canvas.itemconfig(AiOvalId, fill=AiBaseColor))
