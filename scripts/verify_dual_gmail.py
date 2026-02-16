import os
import sys
from pathlib import Path

# Add mail_agent to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'mail_agent'))

try:
    from gmail_service import get_gmail_service
except ImportError as e:
    print(f"Error: Could not import gmail_service: {e}")
    sys.exit(1)

def verify_account(account_type, expected_email):
    print(f"\nVerifying '{account_type}' account...")
    try:
        service = get_gmail_service(account_type)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        print(f"Authenticated as: {email}")
        
        if email.lower() == expected_email.lower():
            print(f"SUCCESS: '{account_type}' is correctly authenticated as {expected_email}.")
            return True
        else:
            print(f"ERROR: '{account_type}' is authenticated as {email}, expected {expected_email}!")
            return False
            
    except Exception as e:
        print(f"FAILED to verify '{account_type}': {e}")
        return False

def main():
    print("--- Gmail Dual-Account Verification ---")
    
    fetch_ok = verify_account('fetch', 'rajavreddy.g@gmail.com')
    send_ok = verify_account('send', 'campusouting.go@gmail.com')
    
    if fetch_ok and send_ok:
        print("\nOVERALL STATUS: SUCCESS - Both accounts are correctly configured.")
    else:
        print("\nOVERALL STATUS: FAILED - Please check the errors above.")

if __name__ == "__main__":
    main()
