import tkinter as tk

BackgroundColor = "#0f1117"
LineColor = "#2a2e3a"
DotColor = "#4b5163"
LabelColor = "#c7cbd6"
AiColor = "#4b6bfb"
YouColor = "#3f4658"
HighlightColor = "#22c55e"
TextColor = "#e5e7eb"


class NetworkMap:
    def __init__(self, Parent, ToolNames, Width=260, Height=460):
        self.Width = Width
        self.Height = Height
        self.Canvas = tk.Canvas(Parent, width=Width, height=Height, bg=BackgroundColor, highlightthickness=0)
        self.Canvas.pack(fill="both", expand=True)

        self.Hubs = {}   # "You"/"AI" -> (OvalId, BaseColor)
        self.Dots = {}   # ToolName -> (OvalId, BaseColor)
        self.Edges = {}  # ToolName -> LineId (AI -> that tool's dot)

        self.DrawGraph(ToolNames)

    def DrawHub(self, Name, X, Y, Radius, Color):
        OvalId = self.Canvas.create_oval(X - Radius, Y - Radius, X + Radius, Y + Radius, fill=Color, outline="")
        self.Canvas.create_text(X, Y, text=Name, fill=TextColor, font=("Segoe UI", 10, "bold"))
        self.Hubs[Name] = (OvalId, Color)

    def DrawGraph(self, ToolNames):
        CenterX = self.Width // 2
        AiY = 75
        YouY = 25

        self.DrawHub("You", CenterX, YouY, 20, YouColor)
        self.Canvas.create_line(CenterX, YouY + 20, CenterX, AiY - 30, fill=LineColor, width=2)
        self.DrawHub("AI", CenterX, AiY, 30, AiColor)

        DotX = 30
        LabelX = 48
        RowHeight = 46
        StartY = 150

        for Index, ToolName in enumerate(ToolNames):
            RowY = StartY + Index * RowHeight

            LineId = self.Canvas.create_line(CenterX, AiY + 25, DotX, RowY, fill=LineColor, width=2)
            self.Edges[ToolName] = LineId

            DotId = self.Canvas.create_oval(
                DotX - 8, RowY - 8, DotX + 8, RowY + 8, fill=DotColor, outline=""
            )
            self.Dots[ToolName] = (DotId, DotColor)

            self.Canvas.create_text(
                LabelX, RowY, text=ToolName, fill=LabelColor, font=("Segoe UI", 9), anchor="w"
            )

    def Activate(self, ToolName):
        if ToolName not in self.Dots:
            return

        DotId, _BaseColor = self.Dots[ToolName]
        self.Canvas.itemconfig(DotId, fill=HighlightColor)

        LineId = self.Edges.get(ToolName)
        if LineId:
            self.Canvas.itemconfig(LineId, fill=HighlightColor, width=3)

        AiOvalId, AiBaseColor = self.Hubs["AI"]
        self.Canvas.itemconfig(AiOvalId, fill=HighlightColor)

        self.Canvas.after(900, self.Deactivate, ToolName, AiBaseColor)

    def Deactivate(self, ToolName, AiBaseColor):
        DotId, BaseColor = self.Dots[ToolName]
        self.Canvas.itemconfig(DotId, fill=BaseColor)

        LineId = self.Edges.get(ToolName)
        if LineId:
            self.Canvas.itemconfig(LineId, fill=LineColor, width=2)

        AiOvalId, _OldColor = self.Hubs["AI"]
        self.Canvas.itemconfig(AiOvalId, fill=AiBaseColor)

    def PulseThinking(self):
        AiOvalId, AiBaseColor = self.Hubs["AI"]
        self.Canvas.itemconfig(AiOvalId, fill=HighlightColor)
        self.Canvas.after(400, lambda: self.Canvas.itemconfig(AiOvalId, fill=AiBaseColor))
