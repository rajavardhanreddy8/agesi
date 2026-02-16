import os
import sys
import json
from pathlib import Path

# Add mail_agent to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'mail_agent'))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: Google Auth libraries not installed.")
    sys.exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def authenticate(account_type):
    """
    Authenticate a specific account type.
    account_type: 'fetch' or 'send'
    """
    token_filename = f'token_{account_type}.json'
    token_path = BASE_DIR / 'mail_agent' / token_filename
    credentials_path = BASE_DIR / 'mail_agent' / 'credentials.json'
    
    print(f"\n--- Authenticating '{account_type}' account ---")
    if account_type == 'fetch':
        expected_email = "rajavreddy.g@gmail.com"
        print(f"Please log in as: {expected_email}")
    elif account_type == 'send':
        expected_email = "campusouting.go@gmail.com"
        print(f"Please log in as: {expected_email}")
    
    if token_path.exists():
        print(f"Removing old token at {token_path}...")
        token_path.unlink()
        
    creds = None
    if credentials_path.exists():
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')
        print("✓ Obtained credentials via OAuth flow")
    else:
        print(f"Error: credentials.json not found at {credentials_path}")
        return

    # Verify Email Identity
    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    email = profile.get('emailAddress')
    
    print(f"Authenticated as: {email}")
    
    if expected_email and email.lower() != expected_email.lower():
        print(f"WARNING: You logged in as {email}, but we expected {expected_email}!")
        confirm = input("Do you want to save this token anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    # Save Token
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    print(f"SUCCESS: Saved token to {token_path}")

def main():
    print("Select account to authenticate:")
    print("1. Fetch Account (rajavreddy.g@gmail.com)")
    print("2. Send Account (campusouting.go@gmail.com)")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == '1':
        authenticate('fetch')
    elif choice == '2':
        authenticate('send')
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
