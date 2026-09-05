import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from Config import LoadConfig, SaveConfig, AppDir, ConfigPath
from SecretsStore import SecretsStore


class SetupWizard(ctk.CTkToplevel):
    def __init__(self, Root, OnComplete):
        super().__init__(Root)
        self.title("Personal Assistant — Setup")
        self.geometry("420x360")
        self.resizable(False, False)
        self.OnComplete = OnComplete
        self.ConfigDict = LoadConfig()
        self.SecretsStoreInstance = SecretsStore(AppDir)

        self.ProviderVar = tk.StringVar(value=self.ConfigDict.get("LlmProvider", "anthropic"))

        ctk.CTkLabel(self, text="Choose your LLM provider", font=("Segoe UI", 15, "bold")).pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        ctk.CTkRadioButton(
            self, text="Claude (Anthropic API — needs an API key)",
            variable=self.ProviderVar, value="anthropic", command=self.RefreshFields,
        ).pack(anchor="w", padx=20, pady=4)
        ctk.CTkRadioButton(
            self, text="Ollama (local model — needs Ollama installed)",
            variable=self.ProviderVar, value="ollama", command=self.RefreshFields,
        ).pack(anchor="w", padx=20, pady=(4, 16))

        self.FieldContainer = ctk.CTkFrame(self, fg_color="transparent")
        self.FieldContainer.pack(fill="x", padx=20)

        self.AnthropicFrame = ctk.CTkFrame(self.FieldContainer, fg_color="transparent")
        ctk.CTkLabel(self.AnthropicFrame, text="Anthropic API key:", anchor="w").pack(fill="x")
        self.ApiKeyEntry = ctk.CTkEntry(self.AnthropicFrame, show="*")
        self.ApiKeyEntry.pack(fill="x", pady=(4, 0))
        ExistingKey = self.SecretsStoreInstance.Get("ANTHROPIC_API_KEY")
        if ExistingKey:
            self.ApiKeyEntry.insert(0, ExistingKey)

        self.OllamaFrame = ctk.CTkFrame(self.FieldContainer, fg_color="transparent")
        ctk.CTkLabel(self.OllamaFrame, text="Ollama model name:", anchor="w").pack(fill="x")
        self.OllamaModelEntry = ctk.CTkEntry(self.OllamaFrame)
        self.OllamaModelEntry.insert(0, self.ConfigDict.get("OllamaModel", "qwen2.5:7b"))
        self.OllamaModelEntry.pack(fill="x", pady=(4, 0))

        self.RefreshFields()

        ctk.CTkButton(self, text="Save and Continue", command=self.OnSave, height=40).pack(
            pady=25, padx=20, fill="x"
        )

        self.protocol("WM_DELETE_WINDOW", self.OnClose)
        self.grab_set()

    def RefreshFields(self):
        self.AnthropicFrame.pack_forget()
        self.OllamaFrame.pack_forget()
        if self.ProviderVar.get() == "anthropic":
            self.AnthropicFrame.pack(fill="x", pady=(0, 10))
        else:
            self.OllamaFrame.pack(fill="x", pady=(0, 10))

    def OnSave(self):
        Provider = self.ProviderVar.get()
        self.ConfigDict["LlmProvider"] = Provider

        if Provider == "anthropic":
            ApiKey = self.ApiKeyEntry.get().strip()
            if not ApiKey:
                messagebox.showerror("Missing key", "Enter your Anthropic API key, or switch to Ollama.")
                return
            self.SecretsStoreInstance.Set("ANTHROPIC_API_KEY", ApiKey)
        else:
            self.ConfigDict["OllamaModel"] = self.OllamaModelEntry.get().strip() or "qwen2.5:7b"

        SaveConfig(self.ConfigDict)
        self.destroy()
        self.OnComplete()

    def OnClose(self):
        if messagebox.askokcancel("Exit setup", "Setup isn't complete. Close the assistant?"):
            self.master.destroy()


def NeedsSetup():
    ConfigDict = LoadConfig()
    if not os.path.exists(ConfigPath):
        return True

    Provider = os.environ.get("LLM_PROVIDER", ConfigDict.get("LlmProvider", "anthropic"))
    if Provider == "anthropic":
        HasEnvKey = bool(os.environ.get("ANTHROPIC_API_KEY"))
        HasStoredKey = SecretsStore(AppDir).Has("ANTHROPIC_API_KEY")
        return not (HasEnvKey or HasStoredKey)

    return False
