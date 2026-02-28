from mail_agent.gmail_service import get_gmail_service, get_latest_email_content
import re

service = get_gmail_service()
# Find the exact subject first
query = 'subject:WEEKEND OUTING REQUEST'
results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
messages = results.get('messages', [])

if messages:
    msg = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
    headers = msg['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    print('Found the email. Exact subject is:', subject)
    
    # Try the exact same query using the generic function
    data = get_latest_email_content(f'"{subject}"')
    if data:
        print('REGEX LINKS:', data.get('form_links', []))
        if not data.get('form_links'):
            print('--- RAW BODY SNIPPET ---')
            print(data.get('body', '')[:500])
        else:
            print('Body length:', len(data.get('body', '')))
    else:
        print('get_latest_email_content returned None for query')
else:
    print('Email not found in inbox.')
