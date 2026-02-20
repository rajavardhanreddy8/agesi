import os
import sys
from pathlib import Path

# Add paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'mail_agent'))
sys.path.append(str(BASE_DIR / 'form_filler'))

# Import the function
from gmail_service import get_latest_email_content

# Test the sync logic locally
print("=== Testing Email Sync Logic Locally ===\n")

SENDER_QUERY = "from:campusouting.go@gmail.com OR from:rajavreddy.g@gmail.com OR from:student.outing@woxsen.edu.in OR from:me"
print(f"Query: {SENDER_QUERY}\n")

email_data = get_latest_email_content(SENDER_QUERY)

if email_data:
    print("✅ Email found!")
    print(f"Subject: {email_data.get('subject')}")
    print(f"Form Links: {email_data.get('form_links')}")
    print(f"Body (first 200 chars): {email_data.get('body', '')[:200]}...")
    
    # Test date extraction
    import re
    from datetime import datetime, timedelta
    
    combined_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
    date_pattern = re.compile(r'\b(\d{2}[./-]\d{2}[./-]\d{4})\b')
    match = date_pattern.search(combined_text)
    
    if match:
        print(f"\n✅ Date found: {match.group(1)}")
        clean_date = match.group(1).replace('/', '.').replace('-', '.')
        start_obj = datetime.strptime(clean_date, "%d.%m.%Y")
        end_obj = start_obj + timedelta(days=2)
        print(f"Start Date (YYYY-MM-DD): {start_obj.strftime('%Y-%m-%d')}")
        print(f"End Date (YYYY-MM-DD): {end_obj.strftime('%Y-%m-%d')}")
    else:
        print("\n❌ No date found in email")
else:
    print("❌ No email found matching the query")
