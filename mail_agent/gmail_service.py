import os.path
import os
import json
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
    """
    Get Gmail API service, supporting both:
    - Railway deployment (via GMAIL_TOKEN_JSON env var)
    - Local development (via token.json file)
    """
    creds = None
    token_path = os.path.join(SCRIPT_DIR, 'token.json')
    credentials_path = os.path.join(SCRIPT_DIR, 'credentials.json')
    
    # First, try environment variable (for Railway deployment)
    token_json_env = os.getenv('GMAIL_TOKEN_JSON')
    if token_json_env:
        try:
            token_data = json.loads(token_json_env)
            creds = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes', SCOPES)
            )
            print("✓ Loaded Gmail credentials from environment variable")
        except Exception as e:
            print(f"⚠️ Failed to parse GMAIL_TOKEN_JSON: {e}")
            creds = None
    
    # Fallback to file-based token (local development)
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        print("✓ Loaded Gmail credentials from token.json")
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("✓ Refreshed Gmail credentials")
        else:
            # Only works in local development (interactive flow)
            if os.path.exists(credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                # Force 'consent' to ensure we get a refresh_token every time (critical for offline access)
                creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')
                print("✓ Obtained new Gmail credentials via OAuth flow")
            else:
                raise Exception("No valid credentials available. Set GMAIL_TOKEN_JSON env var or run locally first.")
        
        # Save the credentials for the next run (local only)
        if not token_json_env:
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

    def get_body_from_payload(payload):
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                     data = part['body'].get('data')
                     if data:
                         body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                     data = part['body'].get('data')
                     if data:
                         body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'].startswith('multipart/'):
                     body += get_body_from_payload(part)
        elif 'body' in payload and payload['body'].get('data'):
            data = payload['body']['data']
            body += base64.urlsafe_b64decode(data).decode('utf-8')
        return body

    body = get_body_from_payload(payload)
    
    # Regex link extraction
    links = []
    if body:
        # 1. Capture hrefs (HTML)
        href_pattern = re.compile(r'href\s*=\s*[\"\'"]((?:https?://)[^\"\'"]+)')
        links.extend(href_pattern.findall(body))
        
        # 2. Capture raw URLs (Plain text)
        # Matches http/https URLs that are NOT inside an href (simple approximation or just grab all)
        # We can just grab all and deduplicate
        raw_url_pattern = re.compile(r'(https?://[^\s\"\'<>]+)')
        links.extend(raw_url_pattern.findall(body))
        
        # Deduplicate
        links = list(set(links))
    
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
