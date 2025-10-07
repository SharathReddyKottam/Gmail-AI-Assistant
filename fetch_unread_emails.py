from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import base64
from email import message_from_bytes

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_service():
    creds = None
    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "wb") as token:
            pickle.dump(creds, token)
    return build("gmail", "v1", credentials=creds)

def fetch_unread():
    service = get_service()

    # List unread messages
    results = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=5
    ).execute()
    messages = results.get("messages", [])

    if not messages:
        print("✅ No unread emails found.")
        return

    print(f"📨 Found {len(messages)} unread email(s):\n")

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        payload = msg_data["payload"]
        headers = payload["headers"]

        sender = subject = None
        for h in headers:
            if h["name"] == "From":
                sender = h["value"]
            if h["name"] == "Subject":
                subject = h["value"]

        snippet = msg_data.get("snippet", "")
        print(f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}\n{'-'*60}")

if __name__ == "__main__":
    fetch_unread()
