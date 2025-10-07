from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the Gmail API scope — "readonly" means it won't modify anything
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    # Load credentials from the downloaded file
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Build the Gmail service
    service = build("gmail", "v1", credentials=creds)
    
    # List Gmail labels (like INBOX, SENT, etc.)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    print("\n✅ Gmail API connection successful!")
    print("📬 Your labels:")
    for label in labels:
        print("  -", label["name"])

if __name__ == "__main__":
    main()
