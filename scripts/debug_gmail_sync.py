import os
import sys
from pathlib import Path
import base64

# Add mail_agent to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'mail_agent'))

try:
    from gmail_service import get_gmail_service
except ImportError as e:
    print(f"Error: Could not import gmail_service: {e}")
    sys.exit(1)

def list_recent_emails():
    with open('debug_gmail_output.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        print("--- Gmail Inbox Debugger ---")
        print("Checking 'fetch' account (rajavreddy.g@gmail.com)...")
        
        try:
            service = get_gmail_service('fetch')
            
            # 1. Check specific sender query
            target_sender = "student.outing@woxsen.edu.in"
            query = f"from:{target_sender} OR from:campusouting.go@gmail.com OR from:me"
            print(f"\n[Test 1] Searching for emails from: {target_sender} (and others)")
            results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            messages = results.get('messages', [])
            
            if messages:
                print(f"✅ Found {len(messages)} emails from {target_sender}.")
                for msg in messages:
                    m = service.users().messages().get(userId='me', id=msg['id']).execute()
                    headers = m['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    print(f"   - ID: {msg['id']} | Subject: {subject}")
            else:
                print(f"❌ No emails found from {target_sender}.")

            # 2. List ALL recent emails (to see who IS sending emails)
            print(f"\n[Test 2] Listing last 5 emails in Inbox (ANY sender):")
            results = service.users().messages().list(userId='me', maxResults=5).execute()
            messages = results.get('messages', [])
            
            if messages:
                for msg in messages:
                    m = service.users().messages().get(userId='me', id=msg['id']).execute()
                    headers = m['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    print(f"   - From: {sender}")
                    print(f"     Subject: {subject}")
                    print(f"     ID: {msg['id']}")
                    print("     ---")
            else:
                print("❌ Inbox appears empty.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    list_recent_emails()
