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

def get_gmail_service():
    """
    Get Gmail API service, supporting both:
    - Railway deployment (via GMAIL_TOKEN_JSON env var)
    - Local development (via token.json file)
    """
    creds = None
    
    token_filename = 'token.json'
    token_path = os.path.join(SCRIPT_DIR, token_filename)
    # First, try environment variable (for Azure/Docker deployment)
    gmail_token_json = os.getenv('GMAIL_TOKEN_JSON')
    env_error = None
    if not creds and gmail_token_json:
        try:
            import json as _json
            token_data = _json.loads(gmail_token_json)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            print("✓ Loaded Gmail credentials from GMAIL_TOKEN_JSON env var")
        except Exception as e:
            env_error = str(e)
            print(f"Warning: Failed to load GMAIL_TOKEN_JSON env var: {e}")
    
    # Fallback to file-based token (local development)
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, try refreshing.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print(f"✓ Refreshed Gmail credentials")
                # Save refreshed token
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
             raw_env_preview = str(gmail_token_json)[:100] if gmail_token_json else "None"
             raise Exception(f"No valid credentials available. Fallback interactive auth is disabled in production. Env error: {env_error}. Token raw preview: {raw_env_preview}")

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_latest_email_content(query_or_sender):
    service = get_gmail_service()
    
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
        href_pattern = re.compile(r'href\s*=\s*["\']((?:https?://)[^"\']+)')
        links.extend(href_pattern.findall(body))
        
        # 2. Capture raw URLs (Plain text)
        raw_url_pattern = re.compile(r'(https?://[^\s"\'<>]+)')
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

        service = get_gmail_service()
        
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
        
        print(f"Email sent to {to}. Message ID: {send_result['id']}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
