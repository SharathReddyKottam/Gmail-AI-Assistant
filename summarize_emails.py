import os
import pickle
import subprocess
import datetime
import time
import gspread
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ---- 1️⃣ API Scopes ----
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets"
]

# ---- 2️⃣ Authenticate Gmail + Sheets ----
def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "wb") as token:
            pickle.dump(creds, token)
    return creds

# ---- 3️⃣ Gmail Service ----
def get_gmail_service(creds):
    return build("gmail", "v1", credentials=creds)

# ---- 4️⃣ Sheets Service ----
def get_sheets_client(creds):
    return gspread.authorize(creds)

# ---- 5️⃣ Fetch All Unread Emails (Paginated) ----
def fetch_all_unread(service, page_size=100):
    """Fetch all unread emails using pagination."""
    msgs = []
    request = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=page_size
    )
    while request is not None:
        resp = request.execute()
        msgs.extend(resp.get("messages", []))
        request = service.users().messages().list_next(
            previous_request=request, previous_response=resp
        )
    return msgs

# ---- 6️⃣ Local Summarizer using Ollama ----
def summarize_text(text):
    if not text.strip():
        return "(No content to summarize)"
    prompt = f"Summarize this email in 1–2 clear sentences:\n\n{text}"
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout.strip()
        return output if output else "(⚠️ No summary returned)"
    except Exception as e:
        return f"(⚠️ Error running Ollama: {e})"
def categorize_text(summary):
    if not summary.strip():
        return "Uncategorized"
    prompt = f"Classify this email into one of these categories: [Job, Finance, Event, Order, Personal, Other].\n\nEmail summary:\n{summary}\n\nCategory:"
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            text=True,
            capture_output=True,  # capture both stdout and stderr
            timeout=60
        )
        category = result.stdout.strip()
        if not category:
            return "Other"
        # Keep only the first word (avoid full sentences)
        return category.split()[0].capitalize()
    except Exception as e:
        return f"Error: {e}"


# ---- 7️⃣ Main Flow ----
def main():
    print("🔐 Connecting to Gmail & Sheets...")
    creds = get_credentials()
    gmail_service = get_gmail_service(creds)
    sheets_client = get_sheets_client(creds)

    # Replace with your Sheet ID
    SHEET_ID = "1mTotStPswtCYRAfsp54G70Kn4pybgEOHSdcOHa4ig00"
    sheet = sheets_client.open_by_key(SHEET_ID).sheet1

    messages = fetch_all_unread(gmail_service)
    total_unread = len(messages)
    if not messages:
        print("✅ No unread emails to summarize.")
        return

    print(f"📬 Found {total_unread} unread email(s)\n{'='*60}")

    # ---- Limit batch to avoid Gmail throttling ----
    BATCH_SIZE = 5
    if total_unread > BATCH_SIZE:
        print(f"⚙️ Too many unread emails ({total_unread}). Processing first {BATCH_SIZE} this run...")
        messages = messages[:BATCH_SIZE]
    else:
        print(f"⚙️ Processing all {total_unread} unread emails...")

    processed = 0
    marked_read = 0
    saved = 0

    for i, msg in enumerate(messages, start=1):
        print(f"\n⏳ Processing email {i}/{len(messages)} ...")

        try:
            # Fetch message details
            msg_data = gmail_service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()

            headers = msg_data["payload"]["headers"]
            sender = subject = None
            for h in headers:
                if h["name"] == "From":
                    sender = h["value"]
                if h["name"] == "Subject":
                    subject = h["value"]

            snippet = msg_data.get("snippet", "")

            # Summarize email
            summary = summarize_text(snippet)
            print(f"💡 Summary: {summary}")
            category = categorize_text(summary)
            print(f"🏷️ Category: {category}")


            # Record timestamp
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append to Google Sheet
            try:
                sheet.append_row([now, sender, subject, summary, category])
                saved += 1
                print(f"✅ Row added to Google Sheet at {now}")
            except Exception as e:
                print(f"⚠️ Failed to append row: {e}")

            # Mark as read
            try:
                gmail_service.users().messages().modify(
                    userId="me",
                    id=msg["id"],
                    body={"removeLabelIds": ["UNREAD"]}
                ).execute()
                marked_read += 1
                print("📬 Email marked as read.")
            except Exception as e:
                print(f"⚠️ Failed to mark as read: {e}")

            processed += 1

        except Exception as e:
            print(f"⚠️ Error processing message: {e}")

        # Delay to avoid hitting Gmail rate limits
        time.sleep(0.2)

        # Show progress every 25 emails
        if i % 25 == 0:
            print(f"✅ Processed {i} emails so far...")

    # ---- Final summary ----
    print("\n🎉 Run complete!")
    print(f"📊 Summary: {processed} processed | {saved} saved to Sheets | {marked_read} marked as read.")
    print("💡 Re-run the script to process the next batch of unread emails.\n")

if __name__ == "__main__":
    main()
