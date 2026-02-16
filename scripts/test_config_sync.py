
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import re

# Add extraction paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / 'form_filler'))
sys.path.append(str(BASE_DIR / 'mail_agent'))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

try:
    from gmail_service import get_latest_email_content
    print("MATCH: gmail_service imported successfully")
except ImportError as e:
    print(f"ERROR: Could not import gmail_service: {e}")
    sys.exit(1)

def test_sync():
    print("--- Starting Sync Logic Test ---")
    
    # 1. Fetch Email
    SENDER_EMAIL = "rrtradersind@gmail.com"
    print(f"Fetching latest email from {SENDER_EMAIL}...")
    try:
        email_data = get_latest_email_content(SENDER_EMAIL)
    except Exception as e:
        print(f"FAILED to fetch email: {e}")
        return

    if not email_data:
        print("No email found from sender.")
        return

    print(f"Email Subject: {email_data.get('subject')}")
    print(f"Email Body Snippet: {email_data.get('body', '')[:100]}...")

    # 2. Extract Data (Mimicking api.py)
    form_link = None
    if email_data.get('form_links'):
        form_link = email_data['form_links'][0]

    combined_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
    
    # Regex for Date (DD.MM.YYYY)
    date_pattern = re.compile(r'\b(\d{2}\.\d{2}\.\d{4})\b')
    match = date_pattern.search(combined_text)
    start_date = match.group(1) if match else None
    
    end_date = None
    reason = None # simple extraction doesn't get reason without Groq usually

    # Calculate End Date
    if start_date:
        try:
            start_obj = datetime.strptime(start_date, "%d.%m.%Y")
            # Convert to YYYY-MM-DD
            start_date_iso = start_obj.strftime("%Y-%m-%d")
            
            end_obj = start_obj + timedelta(days=2)
            end_date_iso = end_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date parse error: {e}")
            start_date_iso = None
            end_date_iso = None
    else:
        start_date_iso = None
        end_date_iso = None

    print("\n--- Extracted Data (Regex) ---")
    print(f"Form Link: {form_link}")
    print(f"Start Date: {start_date} -> {start_date_iso}")
    print(f"End Date:   {end_date_iso}")

    # 3. Grok Fallback (Mock check)
    if not form_link or not start_date_iso:
        print("\n[INFO] Regex failed to get all data. In production, Grok AI would be called here.")
        # We can try importing Grok if env vars exist
        if os.getenv("GROQ_API_KEY"):
            print("GROQ_API_KEY found, attempting Grok...")
            try:
                from groq_service import process_content_with_groq
                grok_result = process_content_with_groq(email_data)
                print(f"Grok Result: {grok_result}")
            except Exception as e:
                print(f"Grok failed: {e}")
        else:
            print("GROQ_API_KEY not found, skipping Grok test.")

    # 4. DB Update Simulation
    print("\n--- Database Update Simulation ---")
    updates = {}
    if form_link: updates['form_link'] = form_link
    if start_date_iso: updates['start_date'] = start_date_iso
    if end_date_iso: updates['end_date'] = end_date_iso
    updates['default_reason'] = "Home Visit" # Default
    
    print(f"Would update 'system_config' with: {updates}")

if __name__ == "__main__":
    test_sync()
