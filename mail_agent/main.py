from gmail_service import get_latest_email_content

from dotenv import load_dotenv
import os
import re
from datetime import datetime, timedelta

load_dotenv()

SENDER_EMAIL = "guntaka.reddy_2028@woxsen.edu.in"

def extract_start_date(text):
    """Extract the first date mentioned in DD.MM.YYYY format from text."""
    date_pattern = re.compile(r'\b(\d{2}\.\d{2}\.\d{4})\b')
    match = date_pattern.search(text)
    if match:
        return match.group(1)
    return None

def main():
    print(f"Fetching latest email from {SENDER_EMAIL}...")
    email_data = get_latest_email_content(SENDER_EMAIL)
    
    if email_data:
        # Get form link
        form_link = None
        if email_data.get('form_links'):
            form_link = email_data['form_links'][0]  # Get the first form link
        
        # Extract start date from email body
        start_date_str = extract_start_date(email_data.get('body', ''))
        
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
            end_date = start_date + timedelta(days=2)
        
        # Print results
        print(f"\nForm Link: {form_link}")
        print(f"Start Date: {start_date.strftime('%d.%m.%Y') if start_date else 'Not found'}")
        print(f"End Date: {end_date.strftime('%d.%m.%Y') if end_date else 'Not found'}")
    else:
        print("No email found.")

if __name__ == "__main__":
    main()

