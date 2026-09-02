import os
import json
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# One OAuth flow, scoped per-service. Add/remove scopes here to change
# what the whole GoogleWorkspace tool set can touch — Drive read-only,
# Gmail modify (needed to read/draft/send), Sheets read/write.
Scopes = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleAuth:
    def __init__(self, AppDir, CredentialsFileName="credentials.json"):
        self.AppDir = AppDir
        self.CredentialsPath = os.path.join(AppDir, CredentialsFileName)
        self.KeyPath = os.path.join(AppDir, "Data", "token.key")
        self.EncryptedTokenPath = os.path.join(AppDir, "Data", "token.enc")

    def GetOrCreateEncryptionKey(self):
        os.makedirs(os.path.dirname(self.KeyPath), exist_ok=True)
        if os.path.exists(self.KeyPath):
            with open(self.KeyPath, "rb") as KeyFile:
                return KeyFile.read()
        NewKey = Fernet.generate_key()
        with open(self.KeyPath, "wb") as KeyFile:
            KeyFile.write(NewKey)
        return NewKey

    def LoadStoredCredentials(self):
        if not os.path.exists(self.EncryptedTokenPath):
            return None
        FernetInstance = Fernet(self.GetOrCreateEncryptionKey())
        with open(self.EncryptedTokenPath, "rb") as TokenFile:
            Encrypted = TokenFile.read()
        Decrypted = FernetInstance.decrypt(Encrypted)
        return Credentials.from_authorized_user_info(json.loads(Decrypted.decode()), Scopes)

    def SaveCredentials(self, CredentialsObject):
        FernetInstance = Fernet(self.GetOrCreateEncryptionKey())
        TokenJson = CredentialsObject.to_json()
        Encrypted = FernetInstance.encrypt(TokenJson.encode())
        os.makedirs(os.path.dirname(self.EncryptedTokenPath), exist_ok=True)
        with open(self.EncryptedTokenPath, "wb") as TokenFile:
            TokenFile.write(Encrypted)

    def GetCredentials(self):
        CredentialsObject = self.LoadStoredCredentials()

        if CredentialsObject and CredentialsObject.valid:
            return CredentialsObject

        if CredentialsObject and CredentialsObject.expired and CredentialsObject.refresh_token:
            CredentialsObject.refresh(Request())
            self.SaveCredentials(CredentialsObject)
            return CredentialsObject

        if not os.path.exists(self.CredentialsPath):
            raise FileNotFoundError(
                f"'{self.CredentialsPath}' not found. Download OAuth client credentials "
                "from Google Cloud Console (APIs & Services -> Credentials -> Create "
                "OAuth client ID -> Desktop app) and save them as credentials.json "
                "next to Main.py."
            )

        Flow = InstalledAppFlow.from_client_secrets_file(self.CredentialsPath, Scopes)
        CredentialsObject = Flow.run_local_server(port=0)
        self.SaveCredentials(CredentialsObject)
        return CredentialsObject
