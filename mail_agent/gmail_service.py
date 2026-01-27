import os.path
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    token_path = os.path.join(SCRIPT_DIR, 'token.json')
    credentials_path = os.path.join(SCRIPT_DIR, 'credentials.json')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_latest_email_content(sender_email):
    service = get_gmail_service()
    
    # query to filter by sender
    q = f"from:{sender_email}"
    
    # List search results, getting only the latest one (maxResults=1)
    results = service.users().messages().list(userId='me', q=q, maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print(f"No messages found from {sender_email}.")
        return None

    message = messages[0]
    msg = service.users().messages().get(userId='me', id=message['id']).execute()

    payload = msg['payload']
    headers = payload['headers']
    subject = ""
    for h in headers:
        if h['name'] == 'Subject':
            subject = h['value']

    body = ""
    if 'parts' in payload:
        # Prioritize HTML part
        html_part = next((part for part in payload['parts'] if part['mimeType'] == 'text/html'), None)
        text_part = next((part for part in payload['parts'] if part['mimeType'] == 'text/plain'), None)
        
        target_part = html_part if html_part else text_part
        
        if target_part:
            data = target_part['body']['data']
            body += base64.urlsafe_b64decode(data).decode('utf-8')
    elif 'body' in payload:
        data = payload['body']['data']
        body += base64.urlsafe_b64decode(data).decode('utf-8')
    
    # Regex link extraction
    links = []
    if body:
        # Adjusted regex to capture hrefs properly
        link_pattern = re.compile(r'href\s*=\s*[\"\'"]((?:https?://)[^\"\'"]+)')
        links = link_pattern.findall(body)
    
    # Simple HTML stripping
    soup = BeautifulSoup(body, "html.parser")
    text_body = soup.get_text()

    return {
        "subject": subject,
        "body": text_body,
        "raw_body": body,
        "links": links,
        "form_links": [l for l in links if "forms.office.com" in l or "docs.google.com" in l or "forms.gle" in l]
    }
