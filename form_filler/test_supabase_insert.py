import requests
import json

URL = "https://uehkqlamchtdzcusqmhi.supabase.co/rest/v1/users"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVlaGtxbGFtY2h0ZHpjdXNxbWhpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTY1ODg3NiwiZXhwIjoyMDg1MjM0ODc2fQ.5lXH71smnhTBOBEm6LdK2pp35WsKhPNhKdxHtaZLXqk"

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

data = {
    "email": "test_connection_agent@woxsen.edu.in",
    "password_hash": "dummy",
    "outlook_password_encrypted": "dummy", 
    "verification_token": "dummy"
}

print(f"Testing POST to {URL}...")
try:
    response = requests.post(URL, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
