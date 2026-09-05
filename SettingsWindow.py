import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from Config import LoadConfig, SaveConfig


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, Root, OnSystemPromptChanged=None):
        super().__init__(Root)
        self.title("Settings")
        self.geometry("480x560")
        self.minsize(420, 480)
        self.OnSystemPromptChanged = OnSystemPromptChanged

        self.ConfigDict = LoadConfig()
        self.OriginalVoiceInput = self.ConfigDict.get("VoiceInputEnabled", False)
        self.OriginalVoiceOutput = self.ConfigDict.get("VoiceOutputEnabled", False)

        ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 16, "bold")).pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        # --- Voice toggles ---
        VoiceFrame = ctk.CTkFrame(self, fg_color="#1c1f2b", corner_radius=10)
        VoiceFrame.pack(fill="x", padx=20, pady=(0, 12))

        self.VoiceInputVar = tk.BooleanVar(value=self.OriginalVoiceInput)
        ctk.CTkSwitch(
            VoiceFrame, text="Enable voice input (microphone / hold-to-talk)",
            variable=self.VoiceInputVar,
        ).pack(anchor="w", padx=14, pady=(14, 4))

        self.VoiceOutputVar = tk.BooleanVar(value=self.OriginalVoiceOutput)
        ctk.CTkSwitch(
            VoiceFrame, text="Enable AI voice output (speak replies)",
            variable=self.VoiceOutputVar,
        ).pack(anchor="w", padx=14, pady=(4, 6))

        ctk.CTkLabel(
            VoiceFrame, text="Changes to voice settings need an app restart to take effect.",
            font=("Segoe UI", 10), text_color="#8a8f9e", anchor="w", justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 14))

        # --- Activation phrase ---
        PhraseFrame = ctk.CTkFrame(self, fg_color="#1c1f2b", corner_radius=10)
        PhraseFrame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            PhraseFrame, text="Activation phrase", font=("Segoe UI", 12, "bold"), anchor="w"
        ).pack(anchor="w", padx=14, pady=(14, 2))
        ctk.CTkLabel(
            PhraseFrame,
            text="Reserved for future always-listening / wake-word mode. "
            "Push-to-talk works regardless of this setting.",
            font=("Segoe UI", 10), text_color="#8a8f9e", anchor="w", justify="left", wraplength=400,
        ).pack(anchor="w", padx=14, pady=(0, 6))

        self.ActivationPhraseEntry = ctk.CTkEntry(PhraseFrame)
        self.ActivationPhraseEntry.insert(0, self.ConfigDict.get("ActivationPhrase", "hey assistant"))
        self.ActivationPhraseEntry.pack(fill="x", padx=14, pady=(0, 14))

        # --- System prompt ---
        PromptFrame = ctk.CTkFrame(self, fg_color="#1c1f2b", corner_radius=10)
        PromptFrame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        ctk.CTkLabel(
            PromptFrame, text="System prompt (how the assistant behaves)",
            font=("Segoe UI", 12, "bold"), anchor="w",
        ).pack(anchor="w", padx=14, pady=(14, 6))

        self.SystemPromptBox = ctk.CTkTextbox(PromptFrame, wrap="word", font=("Segoe UI", 12))
        self.SystemPromptBox.insert("1.0", self.ConfigDict.get("SystemPrompt", ""))
        self.SystemPromptBox.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # --- Save ---
        ctk.CTkButton(self, text="Save", height=40, command=self.OnSave).pack(
            fill="x", padx=20, pady=(0, 20)
        )

        self.grab_set()

    def OnSave(self):
        NewSystemPrompt = self.SystemPromptBox.get("1.0", "end").strip()
        NewVoiceInput = self.VoiceInputVar.get()
        NewVoiceOutput = self.VoiceOutputVar.get()
        NewActivationPhrase = self.ActivationPhraseEntry.get().strip() or "hey assistant"

        self.ConfigDict["SystemPrompt"] = NewSystemPrompt
        self.ConfigDict["VoiceInputEnabled"] = NewVoiceInput
        self.ConfigDict["VoiceOutputEnabled"] = NewVoiceOutput
        self.ConfigDict["ActivationPhrase"] = NewActivationPhrase
        SaveConfig(self.ConfigDict)

        if self.OnSystemPromptChanged:
            self.OnSystemPromptChanged(NewSystemPrompt)

        VoiceChanged = (
            NewVoiceInput != self.OriginalVoiceInput or NewVoiceOutput != self.OriginalVoiceOutput
        )
        if VoiceChanged:
            messagebox.showinfo("Saved", "Saved. Restart the app for the voice changes to take effect.")
        else:
            messagebox.showinfo("Saved", "Settings saved.")

        self.destroy()
