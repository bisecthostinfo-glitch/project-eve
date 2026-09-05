import os
import json
from cryptography.fernet import Fernet


class SecretsStore:
    def __init__(self, AppDir):
        self.KeyPath = os.path.join(AppDir, "Data", "secrets.key")
        self.StorePath = os.path.join(AppDir, "Data", "secrets.enc")

    def GetOrCreateEncryptionKey(self):
        os.makedirs(os.path.dirname(self.KeyPath), exist_ok=True)
        if os.path.exists(self.KeyPath):
            with open(self.KeyPath, "rb") as KeyFile:
                return KeyFile.read()
        NewKey = Fernet.generate_key()
        with open(self.KeyPath, "wb") as KeyFile:
            KeyFile.write(NewKey)
        return NewKey

    def LoadAll(self):
        if not os.path.exists(self.StorePath):
            return {}
        FernetInstance = Fernet(self.GetOrCreateEncryptionKey())
        with open(self.StorePath, "rb") as StoreFile:
            Encrypted = StoreFile.read()
        Decrypted = FernetInstance.decrypt(Encrypted)
        return json.loads(Decrypted.decode())

    def SaveAll(self, SecretsDict):
        FernetInstance = Fernet(self.GetOrCreateEncryptionKey())
        Encrypted = FernetInstance.encrypt(json.dumps(SecretsDict).encode())
        os.makedirs(os.path.dirname(self.StorePath), exist_ok=True)
        with open(self.StorePath, "wb") as StoreFile:
            StoreFile.write(Encrypted)

    def Get(self, Key, Default=None):
        return self.LoadAll().get(Key, Default)

    def Set(self, Key, Value):
        AllSecrets = self.LoadAll()
        AllSecrets[Key] = Value
        self.SaveAll(AllSecrets)

    def Has(self, Key):
        return Key in self.LoadAll()
