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
print("===# Test searching for valid config emails sent to campusouting.go@gmail.com")

SENDER_QUERY = '(from:student.outing@woxsen.edu.in OR from:rajavreddy.g@gmail.com OR from:campusouting.go@gmail.com OR from:me) -subject:"System Test" -subject:"Test Sync Notification"'
print(f"Query: {SENDER_QUERY}\n")

email_data = get_latest_email_content(SENDER_QUERY)

if email_data:
    print("✅ Email found!")
    print(f"Subject: {email_data.get('subject')}")
    print(f"Form Links: {email_data.get('form_links')}")
    # print(f"Body (first 200 chars): {email_data.get('body', '')[:200]}...")
    
    # print("\n---------- ALL LINKS FOUND IN EMAIL -----------")
    # for l in email_data.get('links', []):
    #     print("LINK:", l)
    # print("-----------------------------------------------")

    with open('email_body.txt', 'w', encoding='utf-8') as f:
        f.write("RAW BODY:\n")
        f.write(email_data.get('raw_body', ''))
        f.write("\n\nPARSED TEXT:\n")
        f.write(email_data.get('body', ''))
        f.write(f"\n\nFINAL FORM LINKS: {email_data.get('form_links')}")
        f.write(f"\nALL LINKS FOUND: {email_data.get('links')}")

    # The backend strictly checks for form_links array
    from datetime import datetime, timedelta
    
    form_link = None
    start_date = None
    end_date = None
    reason = None

    try:
        from mail_agent.groq_service import process_content_with_groq
        print("DEBUG: Using Groq AI for primary data extraction...")
        grok_result = process_content_with_groq(email_data)
        if grok_result:
            print(f"Groq Extraction Result: {grok_result}")
            start_date_raw = grok_result.get('start_date')
            if start_date_raw:
                try:
                    s_obj = datetime.strptime(start_date_raw, "%d.%m.%Y")
                    start_date = s_obj.strftime("%Y-%m-%d")
                except:
                    try:
                        s_obj = datetime.strptime(start_date_raw, "%Y-%m-%d")
                        start_date = s_obj.strftime("%Y-%m-%d")
                    except:
                        pass
                
                if start_date:
                    end_date = (s_obj + timedelta(days=2)).strftime("%Y-%m-%d")

            if grok_result.get('form_link'):
                form_link = grok_result['form_link']
            
            if grok_result.get('reason'):
                reason = grok_result['reason']
    except Exception as e:
        print(f"Groq API extraction failed: {e}")

    # Fallbacks
    if not form_link and email_data.get('form_links'):
        form_link = email_data['form_links'][0]

    if not start_date:
        import re
        combined_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        date_pattern = re.compile(r'\b(\d{2}[./-]\d{2}[./-]\d{4})\b')
        match = date_pattern.search(combined_text)
        if match:
            raw_d = match.group(1)
            clean_date = raw_d.replace('/', '.').replace('-', '.')
            try:
                s_obj = datetime.strptime(clean_date, "%d.%m.%Y")
                start_date = s_obj.strftime("%Y-%m-%d")
                end_date = (s_obj + timedelta(days=2)).strftime("%Y-%m-%d")
            except:
                pass

    with open('test_results.txt', 'w', encoding='utf-8') as f:
        if start_date:
            f.write(f"\n✅ Date found: {start_date}")
            f.write(f"\nStart Date (YYYY-MM-DD): {start_date}")
            f.write(f"\nEnd Date (YYYY-MM-DD): {end_date}")
        else:
            f.write("\n❌ No date found in email")

        if form_link:
            f.write(f"\n✅ Form Link found: {form_link}")
        else:
            f.write("\n❌ No Form Link found")
            
        f.write(f"\nReason: {reason or 'Home Visit'}")
        
    print("✅ Results written to test_results.txt")
else:
    print("❌ No email found matching the query")
