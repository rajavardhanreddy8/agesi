import os.path
import os
import json
import base64
import re
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    Request = Credentials = InstalledAppFlow = build = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_gmail_service(account_type='fetch'):
    """
    Get Gmail API service, supporting both:
    - Railway deployment (via GMAIL_TOKEN_JSON env var)
    - Local development (via token.json file)
    
    account_type: 'fetch' (rajavreddy.g) or 'send' (campusouting.go)
    """
    creds = None
    
    # Define token file based on account type
    if account_type == 'fetch':
        token_filename = 'token_fetch.json'
    elif account_type == 'send':
        token_filename = 'token_send.json'
    else:
        # Default fallback or error
        token_filename = 'token_fetch.json' 

    token_path = os.path.join(SCRIPT_DIR, token_filename)
    credentials_path = os.path.join(SCRIPT_DIR, 'credentials.json')
    
    # First, try environment variable (for Railway deployment)
    # TODO: Update Railway to support dual tokens (maybe GMAIL_TOKEN_FETCH_JSON, GMAIL_TOKEN_SEND_JSON)
    # For now, we prioritize local file for this specific request
    
    # Fallback to file-based token (local development)
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # print(f"✓ Loaded Gmail credentials from {token_filename}")
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print(f"✓ Refreshed Gmail credentials for {account_type}")
                # Save refreshed token
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None

        if not creds:
            # Only works in local development (interactive flow)
            if os.path.exists(credentials_path):
                print(f"Initiating OAuth flow for {account_type}...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                # Force 'consent' to ensure we get a refresh_token every time (critical for offline access)
                creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')
                print(f"✓ Obtained new Gmail credentials for {account_type}")
                
                 # Save the credentials for the next run (local only)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            else:
                raise Exception(f"No valid credentials available for {account_type}. Set env var or run locally first.")

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_latest_email_content(query_or_sender):
    service = get_gmail_service('fetch')
    
    # query to filter by sender or specific query
    if "from:" in query_or_sender or " OR " in query_or_sender:
        q = query_or_sender
    else:
        q = f"from:{query_or_sender}"
    
    # List search results, getting only the latest one (maxResults=1)
    results = service.users().messages().list(userId='me', q=q, maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print(f"No messages found matching: {query_or_sender}")
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

def send_email(to, subject, body, html_body=None, attachments=None):
    """Send an email using Gmail API"""
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        import mimetypes
        import base64

        service = get_gmail_service('send')
        
        message = MIMEMultipart('alternative') if not attachments else MIMEMultipart('mixed')
        message['Subject'] = subject
        message['From'] = 'me'
        message['To'] = to
        
        if html_body:
            msg_alt = MIMEMultipart('alternative')
            msg_alt.attach(MIMEText(body, 'plain'))
            msg_alt.attach(MIMEText(html_body, 'html'))
            message.attach(msg_alt)
        else:
            message.attach(MIMEText(body, 'plain'))
            
        if attachments:
            for filepath in attachments:
                if not filepath or not os.path.exists(filepath):
                    continue
                content_type, encoding = mimetypes.guess_type(filepath)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                main_type, sub_type = content_type.split('/', 1)
                
                with open(filepath, 'rb') as fp:
                    attachment_part = MIMEBase(main_type, sub_type)
                    attachment_part.set_payload(fp.read())
                
                encoders.encode_base64(attachment_part)
                filename = os.path.basename(filepath)
                attachment_part.add_header('Content-Disposition', 'attachment', filename=filename)
                message.attach(attachment_part)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        send_result = service.users().messages().send(
            userId='me', 
            body={'raw': raw_message}
        ).execute()
        
        print(f"✓ Email sent to {to}. Message ID: {send_result['id']}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
