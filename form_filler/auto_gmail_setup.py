import os
import sys
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
import threading

def main():
    client_id = sys.argv[1].strip()
    client_secret = sys.argv[2].strip()

    # The exact URI configured in Google Cloud Console
    redirect_uri = "http://localhost:8080"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={urllib.parse.quote(client_id)}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/gmail.readonly&"
        f"access_type=offline&prompt=consent"
    )

    auth_code = [None]

    class OAuthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if 'code' in params:
                auth_code[0] = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication successful!</h1><p>You can close this window now and return to the chat.</p></body></html>")
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Error</h1><p>No code found.</p></body></html>")

        def log_message(self, format, *args):
            pass

    server = HTTPServer(('localhost', 8080), OAuthHandler)
    
    # Open browser automatically
    print(f"\nOpening browser for Google Authentication...")
    webbrowser.open_new(auth_url)
    
    # Wait for the single request containing the code
    server.handle_request()
    
    code = auth_code[0]
    if not code:
        print("Failed to get authorization code.")
        sys.exit(1)

    print("\nGot authorization code! Exchanging for Refresh Token...")

    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }).encode('utf-8')
    
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            refresh_token = result.get('refresh_token')
            if not refresh_token:
                print("FAILED: Google did not return a refresh token.")
                sys.exit(1)
            
            creds_text = f"GMAIL_CLIENT_ID={client_id}\nGMAIL_CLIENT_SECRET={client_secret}\nGMAIL_REFRESH_TOKEN={refresh_token}\n"
            
            with open('.env.gmail', 'w') as f:
                f.write(creds_text)
                
            print("\n" + "=" * 60)
            print("SUCCESS! Credentials saved to .env.gmail")
            print("=" * 60)
            
            # Save it directly if possible or just output it
    except Exception as e:
        print(f"ERROR exchanging code: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))

if __name__ == '__main__':
    main()
