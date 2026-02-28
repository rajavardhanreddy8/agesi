from mail_agent.gmail_service import get_gmail_service, get_latest_email_content
service = get_gmail_service()
query = 'from:student.outing@woxsen.edu.in OR from:rajavreddy.g@gmail.com OR from:campusouting.go@gmail.com OR from:me'
results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
messages = results.get('messages', [])
for i, m in enumerate(messages):
    print(f'\n--- EMAIL {i+1} ---')
    msg = service.users().messages().get(userId='me', id=m['id']).execute()
    headers = msg['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'No Sender')
    print(f'FROM: {sender}')
    print(f'SUBJECT: {subject}')
    
    # Try to extract data as if it were the latest email
    # A bit hacky but we just want to see what bridge.py would see
    data = get_latest_email_content(f'subject:"{subject}"')
    if data:
         print(f'REGEX LINKS: {data.get("form_links", [])}')
         from mail_agent.bridge import process_content_with_groq
         try:
             res = process_content_with_groq(data)
             print(f'GROQ EXTRACT: {res}')
         except Exception as e:
             print(f'GROQ ERROR: {e}')
    else:
        print('Extraction failed to find email locally.')
        
