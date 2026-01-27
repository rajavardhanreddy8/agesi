from gmail_service import get_latest_email_content
import json
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = "guntaka.reddy_2028@woxsen.edu.in"
# Output path: into the doc_handle/public folder
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'doc_handle', 'public', 'outing_data.json')

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
            try:
                start_obj = datetime.strptime(start_date_str, "%d.%m.%Y")
                start_date = start_date_str # Keep DD.MM.YYYY format
                end_obj = start_obj + timedelta(days=2)
                end_date = end_obj.strftime("%d.%m.%Y")
            except Exception as e:
                print(f"Date parse error: {e}")
        
        output_data = {
            "form_link": form_link,
            "start_date": start_date,
            "end_date": end_date,
            "extracted_at": datetime.now().isoformat()
        }

        # Write to JSON file
        try:
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Successfully exported extracted data to: {OUTPUT_FILE}")
            print(json.dumps(output_data, indent=2))
        except Exception as e:
            print(f"Error writing output file: {e}")

    else:
        print("No email found.")

if __name__ == "__main__":
    main()
