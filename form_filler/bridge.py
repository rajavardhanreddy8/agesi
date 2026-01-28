from gmail_service import get_latest_email_content
import json
import os
import re
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = "rrtradersind@gmail.com"

# Endpoint to trigger automation
# Uses BACKEND_URL env var for Railway internal networking
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
BACKEND_TRIGGER_URL = f"{BACKEND_BASE_URL}/api/auto-submit-from-email"

def extract_start_date(text):
    """Extract the first date mentioned in DD.MM.YYYY format from text."""
    date_pattern = re.compile(r'\b(\d{2}\.\d{2}\.\d{4})\b')
    match = date_pattern.search(text)
    if match:
        return match.group(1)
    return None

def main():
    print(f"Fetching latest email from {SENDER_EMAIL}...")
    try:
        email_data = get_latest_email_content(SENDER_EMAIL)
    except Exception as e:
        print(f"Error fetching email: {e}")
        return

    if email_data:
        # Get form link
        form_link = None
        if email_data.get('form_links'):
            form_link = email_data['form_links'][0]  # Get the first form link
        
        # Extract start date from email body or subject
        combined_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        start_date_str = extract_start_date(combined_text)
        
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
        
        if not form_link or not start_date:
            print(f"Regex extraction failed. Date: {start_date}, Link: {form_link}")
            print(f"Attempting Grok AI fallback...")
            
            try:
                from groq_service import process_content_with_groq
                grok_result = process_content_with_groq(email_data)
                
                if grok_result:
                    print(f"Grok Result: {grok_result}")
                    if not start_date and grok_result.get('start_date'):
                        try:
                            # Verify format
                            datetime.strptime(grok_result['start_date'], "%d.%m.%Y")
                            start_date = grok_result['start_date']
                            # Recalculate end date
                            s_obj = datetime.strptime(start_date, "%d.%m.%Y")
                            end_date = (s_obj + timedelta(days=2)).strftime("%d.%m.%Y")
                        except:
                            print("Grok returned invalid date format")
                    
                    if not form_link and grok_result.get('form_link'):
                        form_link = grok_result['form_link']
            except Exception as e:
                print(f"Grok fallback failed: {e}")

        if not form_link or not start_date:
            print(f"Missing data after fallback. Link: {form_link}, Date: {start_date}")
            print(f"Subject: {email_data.get('subject')}")
            print(f"Body snippet: {email_data.get('body', '')[:500]}")
            return

        print(f"\nExtracted Data:\nLink: {form_link}\nStart: {start_date}\nEnd: {end_date}")

        # Trigger Backend Automation
        payload = {
            "form_url": form_link,
            "start_date": start_date,
            "end_date": end_date
        }
        
        print(f"Triggering backend automation at {BACKEND_TRIGGER_URL}...")
        try:
            response = requests.post(BACKEND_TRIGGER_URL, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[OK] Success! Backend response: {response.json()}")
            else:
                print(f"[ERROR] Backend failed ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"[ERROR] Connection error to backend: {e}")
            print("Ensure the Flask app is running at http://localhost:5000")

    else:
        print("No email found.")

if __name__ == "__main__":
    main()
