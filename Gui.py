import os
import threading
import tkinter as tk
import customtkinter as ctk

from Config import LoadConfig
from Logger import ActionLogger
from AgentLoop import AgentLoop
from Main import BuildProvider, BuildToolRegistry
from AudioRecorder import AudioRecorder
from SpeechToText import SpeechToText
from TextToSpeech import TextToSpeech
from SetupWizard import SetupWizard, NeedsSetup
from NetworkMap import NetworkMap

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AssistantGui:
    def __init__(self, Root):
        self.Root = Root
        self.Root.title("Personal Assistant")
        self.Root.geometry("980x640")
        self.Root.minsize(760, 480)

        self.ConfigDict = LoadConfig()
        self.Provider = BuildProvider(self.ConfigDict)
        self.ToolRegistry = BuildToolRegistry(self.ConfigDict)
        self.ActionLoggerInstance = ActionLogger(self.ConfigDict["ActionLogPath"])

        if "FileSearch" in self.ToolRegistry:
            self.ToolRegistry["FileSearch"].RebuildIndex()

        self.Loop = AgentLoop(
            Provider=self.Provider,
            ToolRegistry=self.ToolRegistry,
            ActionLogger=self.ActionLoggerInstance,
            MaxToolCalls=self.ConfigDict["MaxToolCallsPerRequest"],
            SystemPrompt=self.ConfigDict["SystemPrompt"],
            OnToolCall=self.OnToolCallFromLoop,
        )
        self.ConversationHistory = []

        self.SpeechToTextInstance = None
        self.Recorder = None
        self.TextToSpeechInstance = None
        self.SetUpVoice()

        self.BuildLayout()

    def SetUpVoice(self):
        if not self.ConfigDict.get("VoiceEnabled"):
            return

        try:
            self.SpeechToTextInstance = SpeechToText(self.ConfigDict.get("WhisperModelSize", "base.en"))
            self.Recorder = AudioRecorder()
        except Exception as ErrorObject:
            print(f"STT setup failed, voice input disabled: {ErrorObject}")

        try:
            VoiceModelPath = self.ConfigDict.get("PiperVoiceModelPath")
            if VoiceModelPath and os.path.exists(VoiceModelPath):
                self.TextToSpeechInstance = TextToSpeech(
                    VoiceModelPath, self.ConfigDict.get("PiperVoiceConfigPath")
                )
            else:
                print(f"Piper voice model not found at '{VoiceModelPath}'. Run SetupPiper.ps1. TTS disabled.")
        except Exception as ErrorObject:
            print(f"TTS setup failed, voice output disabled: {ErrorObject}")

    def BuildLayout(self):
        self.Root.grid_columnconfigure(0, weight=1)
        self.Root.grid_columnconfigure(1, weight=0)
        self.Root.grid_rowconfigure(0, weight=1)

        # --- Left: chat panel ---
        ChatPanel = ctk.CTkFrame(self.Root, corner_radius=0)
        ChatPanel.grid(row=0, column=0, sticky="nsew")
        ChatPanel.grid_rowconfigure(0, weight=1)
        ChatPanel.grid_columnconfigure(0, weight=1)

        self.ChatLog = ctk.CTkTextbox(
            ChatPanel, wrap="word", state="disabled", font=("Segoe UI", 13),
            fg_color="#161923", corner_radius=12,
        )
        self.ChatLog.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 8))
        self.ChatLog.tag_config("user", foreground="#9db4ff")
        self.ChatLog.tag_config("assistant", foreground="#c9cdd8")

        InputRow = ctk.CTkFrame(ChatPanel, fg_color="transparent")
        InputRow.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        InputRow.grid_columnconfigure(0, weight=1)

        self.InputEntry = ctk.CTkEntry(
            InputRow, placeholder_text="Type a message...", height=40, corner_radius=10
        )
        self.InputEntry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.InputEntry.bind("<Return>", lambda Event: self.OnSend())

        SendButton = ctk.CTkButton(InputRow, text="Send", width=80, height=40, command=self.OnSend)
        SendButton.grid(row=0, column=1, padx=(0, 8))

        if self.SpeechToTextInstance:
            TalkButton = ctk.CTkButton(InputRow, text="Hold to Talk", width=120, height=40, fg_color="#3a3f52")
            TalkButton.grid(row=0, column=2)
            TalkButton.bind("<ButtonPress-1>", self.OnTalkStart)
            TalkButton.bind("<ButtonRelease-1>", self.OnTalkStop)

        BottomRow = ctk.CTkFrame(ChatPanel, fg_color="transparent")
        BottomRow.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        BottomRow.grid_columnconfigure(0, weight=1)

        self.StatusLabel = ctk.CTkLabel(BottomRow, text="Ready", text_color="#7f8696", anchor="w")
        self.StatusLabel.grid(row=0, column=0, sticky="w")

        self.MuteVar = tk.BooleanVar(value=not bool(self.TextToSpeechInstance))
        MuteSwitch = ctk.CTkSwitch(BottomRow, text="Mute voice", variable=self.MuteVar, onvalue=True, offvalue=False)
        MuteSwitch.grid(row=0, column=1, sticky="e")

        # --- Right: live network map panel ---
        MapPanel = ctk.CTkFrame(self.Root, width=240, corner_radius=0, fg_color="#0f1117")
        MapPanel.grid(row=0, column=1, sticky="ns")
        MapPanel.grid_propagate(False)

        MapTitle = ctk.CTkLabel(MapPanel, text="Activity", font=("Segoe UI", 13, "bold"), text_color="#9aa0ad")
        MapTitle.pack(padx=16, pady=(20, 4), anchor="w")

        ToolNames = list(self.ToolRegistry.keys())
        self.Map = NetworkMap(MapPanel, ToolNames, Width=220, Height=460)

    def AppendChat(self, Speaker, Text):
        Tag = "user" if Speaker == "You" else "assistant"
        self.ChatLog.configure(state="normal")
        self.ChatLog.insert("end", f"{Speaker}\n", (Tag,))
        self.ChatLog.insert("end", f"{Text}\n\n")
        self.ChatLog.configure(state="disabled")
        self.ChatLog.see("end")

    def SetStatus(self, Text):
        self.StatusLabel.configure(text=Text)

    def OnToolCallFromLoop(self, ToolName):
        # Called from the background request thread — hop to the main thread for UI updates.
        self.Root.after(0, self.Map.Activate, ToolName)
        self.Root.after(0, self.SetStatus, f"Using {ToolName}...")

    def OnSend(self):
        if self.Provider is None:
            self.AppendChat(
                "Assistant",
                "No LLM provider configured — check your API key or Ollama settings, then restart.",
            )
            return

        UserText = self.InputEntry.get().strip()
        if not UserText:
            return
        self.InputEntry.delete(0, "end")
        self.AppendChat("You", UserText)
        self.SetStatus("Thinking...")
        self.Map.PulseThinking()
        threading.Thread(target=self.RunRequest, args=(UserText,), daemon=True).start()

    def RunRequest(self, UserText):
        try:
            Result = self.Loop.HandleRequest(UserText, self.ConversationHistory)
            self.ConversationHistory = Result["Messages"]
            ResponseText = Result["FinalResponse"] or "(no response text)"
        except Exception as ErrorObject:
            ResponseText = f"Something went wrong: {ErrorObject}"

        self.Root.after(0, self.OnResponseReady, ResponseText)

    def OnResponseReady(self, ResponseText):
        self.AppendChat("Assistant", ResponseText)
        self.SetStatus("Ready")
        if self.TextToSpeechInstance and not self.MuteVar.get():
            threading.Thread(
                target=self.TextToSpeechInstance.Speak, args=(ResponseText,), daemon=True
            ).start()

    def OnTalkStart(self, _Event):
        if not self.Recorder:
            return
        self.SetStatus("Listening...")
        self.Recorder.StartRecording()

    def OnTalkStop(self, _Event):
        if not self.Recorder:
            return
        self.SetStatus("Transcribing...")
        AudioArray = self.Recorder.StopRecording()
        threading.Thread(target=self.TranscribeAndSend, args=(AudioArray,), daemon=True).start()

    def TranscribeAndSend(self, AudioArray):
        if AudioArray.size == 0:
            self.Root.after(0, self.SetStatus, "Ready")
            return

        Text = self.SpeechToTextInstance.Transcribe(AudioArray)
        if not Text:
            self.Root.after(0, self.SetStatus, "Didn't catch that — try again")
            return

        self.Root.after(0, self.OnTranscribed, Text)

    def OnTranscribed(self, Text):
        self.InputEntry.delete(0, "end")
        self.InputEntry.insert(0, Text)
        self.OnSend()


def Main():
    ctk.set_appearance_mode("dark")
    Root = ctk.CTk()
    Root.withdraw()  # hide the main window until setup (if needed) is done

    def LaunchAssistant():
        Root.deiconify()
        AssistantGui(Root)

    if NeedsSetup():
        SetupWizard(Root, OnComplete=LaunchAssistant)
    else:
        LaunchAssistant()

    Root.mainloop()


if __name__ == "__main__":
    Main()
