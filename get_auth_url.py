import os
import sys

# Change to the current directory to correctly find mail_agent/
base_dir = r"C:\Users\admin\Documents\outing\agent 4.0"
os.chdir(base_dir)
sys.path.append(os.path.join(base_dir, 'mail_agent'))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

flow = InstalledAppFlow.from_client_secrets_file('mail_agent/credentials.json', SCOPES)

print("Starting local server for authentication...")
print("This will AUTOMATICALLY open your default web browser.")
print("If the browser opens, please select campusouting.go@gmail.com to login.")

# This automatically opens the browser using webbrowser.open() inside the flow
try:
    creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline', open_browser=True)
    
    with open('mail_agent/token_send.json', 'w') as token:
        token.write(creds.to_json())
    
    print('SUCCESS! Token saved.')
except Exception as e:
    print(f"Error occurred: {e}")
