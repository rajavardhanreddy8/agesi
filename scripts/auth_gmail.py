
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

def main():
    print("--- Gmail Authentication Script ---")
    print("This script will open a browser to authenticate 'campusouting.go@gmail.com'.")
    print("Ensure 'mail_agent/credentials.json' is present.")
    
    token_path = BASE_DIR / 'mail_agent' / 'token.json'
    if token_path.exists():
        print(f"Removing old token at {token_path}...")
        token_path.unlink()
        
    try:
        # get_gmail_service() will trigger flow.run_local_server() if token is missing
        service = get_gmail_service()
        print("\nSUCCESS: Authentication complete!")
        print(f"New token saved to: {token_path}")
    except Exception as e:
        print(f"\nFAILED: {e}")

if __name__ == "__main__":
    main()
