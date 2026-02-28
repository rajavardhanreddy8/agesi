import os
import json
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

with open('mail_agent/token.json') as f:
    gmail_token_json = f.read()

print('Loading...', gmail_token_json[:50])
try:
    token_data = json.loads(gmail_token_json)
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    print('SUCCESS! Valid:', creds.valid, 'Expired:', creds.expired)
except Exception as e:
    print('ERROR:', e)
