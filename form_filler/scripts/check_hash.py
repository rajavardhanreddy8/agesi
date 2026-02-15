
import requests

URL = "https://uehkqlamchtdzcusqmhi.supabase.co/rest/v1/users"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVlaGtxbGFtY2h0ZHpjdXNxbWhpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTY1ODg3NiwiZXhwIjoyMDg1MjM0ODc2fQ.5lXH71smnhTBOBEm6LdK2pp35WsKhPNhKdxHtaZLXqk"

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

params = {
    "select": "id,email,password_hash",
    "email": "eq.guntaka.reddy_2028@woxsen.edu.in"
}

response = requests.get(URL, headers=headers, params=params)

print(f"Status: {response.status_code}")
print(f"Data: {response.json()}")

if response.json():
    user = response.json()[0]
    print(f"\nPassword Hash: {user['password_hash']}")
    print(f"Hash Length: {len(user['password_hash'])}")
    print(f"Starts with $2b$: {user['password_hash'].startswith('$2b$') if user['password_hash'] else 'N/A'}")
