
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('ENCRYPTION_KEY')
print(f"Original Key: '{key}' (Length: {len(key) if key else 0})")

variations = [
    key,
    key[:-1] if key else None, # Remove last char (=)
    key.replace('=', '') if key else None,
]

for v in variations:
    if not v: continue
    try:
        f = Fernet(v.encode())
        print(f"Success: Key '{v}' is VALID. Length: {len(v)}")
    except Exception as e:
        print(f"Failed: Key '{v}' is INVALID: {e}")

# Generate a valid key for reference
new_key = Fernet.generate_key().decode()
print(f"Example valid key: {new_key}")
print(f"Example length: {len(new_key)}")
