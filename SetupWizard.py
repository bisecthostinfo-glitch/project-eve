import os
import tkinter as tk
from tkinter import messagebox

from Config import LoadConfig, SaveConfig, AppDir, ConfigPath
from SecretsStore import SecretsStore


class SetupWizard(tk.Toplevel):
    def __init__(self, Root, OnComplete):
        super().__init__(Root)
        self.title("Personal Assistant — Setup")
        self.resizable(False, False)
        self.OnComplete = OnComplete
        self.ConfigDict = LoadConfig()
        self.SecretsStoreInstance = SecretsStore(AppDir)

        self.ProviderVar = tk.StringVar(value=self.ConfigDict.get("LlmProvider", "anthropic"))

        tk.Label(self, text="Choose your LLM provider:", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", padx=15, pady=(15, 5)
        )

        tk.Radiobutton(
            self, text="Claude (Anthropic API — needs an API key)",
            variable=self.ProviderVar, value="anthropic", command=self.RefreshFields,
        ).pack(anchor="w", padx=15)
        tk.Radiobutton(
            self, text="Ollama (local model — needs Ollama installed and running)",
            variable=self.ProviderVar, value="ollama", command=self.RefreshFields,
        ).pack(anchor="w", padx=15, pady=(0, 10))

        self.AnthropicFrame = tk.Frame(self)
        tk.Label(self.AnthropicFrame, text="Anthropic API key:").pack(anchor="w")
        self.ApiKeyEntry = tk.Entry(self.AnthropicFrame, width=45, show="*")
        self.ApiKeyEntry.pack(fill="x", pady=(2, 0))
        ExistingKey = self.SecretsStoreInstance.Get("ANTHROPIC_API_KEY")
        if ExistingKey:
            self.ApiKeyEntry.insert(0, ExistingKey)

        self.OllamaFrame = tk.Frame(self)
        tk.Label(self.OllamaFrame, text="Ollama model name:").pack(anchor="w")
        self.OllamaModelEntry = tk.Entry(self.OllamaFrame, width=45)
        self.OllamaModelEntry.insert(0, self.ConfigDict.get("OllamaModel", "qwen2.5:7b"))
        self.OllamaModelEntry.pack(fill="x", pady=(2, 0))

        self.FieldContainer = tk.Frame(self)
        self.FieldContainer.pack(fill="x", padx=15)
        self.RefreshFields()

        tk.Button(self, text="Save and Continue", command=self.OnSave).pack(pady=15)

        self.protocol("WM_DELETE_WINDOW", self.OnClose)
        self.grab_set()

    def RefreshFields(self):
        self.AnthropicFrame.pack_forget()
        self.OllamaFrame.pack_forget()
        if self.ProviderVar.get() == "anthropic":
            self.AnthropicFrame.pack(in_=self.FieldContainer, fill="x", pady=(0, 10))
        else:
            self.OllamaFrame.pack(in_=self.FieldContainer, fill="x", pady=(0, 10))

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
