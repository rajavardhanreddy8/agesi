from mail_agent.gmail_service import get_gmail_service

service = get_gmail_service()
query = '(from:student.outing@woxsen.edu.in OR from:rajavreddy.g@gmail.com OR from:campusouting.go@gmail.com OR from:me) ("forms.office.com" OR "Microsoft Forms")'

print(f"Executing query: {query}")
results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
messages = results.get('messages', [])

if messages:
    print(f"Found {len(messages)} matching emails:")
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        print(f" - ID: {m['id']} | Subject: {subject}")
else:
    print('No emails found matching the backend query.')
