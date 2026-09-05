import os
import threading
import tkinter as tk
from tkinter import scrolledtext

from Config import LoadConfig
from Logger import ActionLogger
from AgentLoop import AgentLoop
from Main import BuildProvider, BuildToolRegistry
from AudioRecorder import AudioRecorder
from SpeechToText import SpeechToText
from TextToSpeech import TextToSpeech
from SetupWizard import SetupWizard, NeedsSetup


class AssistantGui:
    def __init__(self, Root):
        self.Root = Root
        self.Root.title("Personal Assistant")

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
        )
        self.ConversationHistory = []

        self.SpeechToTextInstance = None
        self.Recorder = None
        self.TextToSpeechInstance = None
        self.SetUpVoice()
        self.BuildWidgets()

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

    def BuildWidgets(self):
        self.ChatLog = scrolledtext.ScrolledText(
            self.Root, state="disabled", width=80, height=28, wrap="word"
        )
        self.ChatLog.pack(padx=10, pady=10)

        InputFrame = tk.Frame(self.Root)
        InputFrame.pack(fill="x", padx=10, pady=(0, 5))

        self.InputEntry = tk.Entry(InputFrame)
        self.InputEntry.pack(side="left", fill="x", expand=True)
        self.InputEntry.bind("<Return>", lambda Event: self.OnSend())

        SendButton = tk.Button(InputFrame, text="Send", command=self.OnSend)
        SendButton.pack(side="left", padx=(5, 0))

        if self.SpeechToTextInstance:
            TalkButton = tk.Button(InputFrame, text="Hold to Talk")
            TalkButton.pack(side="left", padx=(5, 0))
            TalkButton.bind("<ButtonPress-1>", self.OnTalkStart)
            TalkButton.bind("<ButtonRelease-1>", self.OnTalkStop)

        self.MuteVar = tk.BooleanVar(value=not bool(self.TextToSpeechInstance))
        MuteCheck = tk.Checkbutton(InputFrame, text="Mute", variable=self.MuteVar)
        MuteCheck.pack(side="left", padx=(5, 0))

        self.StatusLabel = tk.Label(self.Root, text="Ready", anchor="w")
        self.StatusLabel.pack(fill="x", padx=10, pady=(0, 10))

    def AppendChat(self, Speaker, Text):
        self.ChatLog.configure(state="normal")
        self.ChatLog.insert("end", f"{Speaker}: {Text}\n\n")
        self.ChatLog.configure(state="disabled")
        self.ChatLog.see("end")

    def SetStatus(self, Text):
        self.StatusLabel.configure(text=Text)

    def OnSend(self):
        if self.Provider is None:
            self.AppendChat(
                "Assistant",
                "No LLM provider configured — check ANTHROPIC_API_KEY or your Ollama settings, then restart.",
            )
            return

        UserText = self.InputEntry.get().strip()
        if not UserText:
            return
        self.InputEntry.delete(0, "end")
        self.AppendChat("You", UserText)
        self.SetStatus("Thinking...")
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
    Root = tk.Tk()
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
