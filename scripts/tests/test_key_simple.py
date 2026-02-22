
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('ENCRYPTION_KEY')
if not key:
    print("NO_KEY")
    exit()

# Try without =
v1 = key.replace('=', '')
try:
    Fernet(v1.encode())
    print(f"VALID_WITHOUT_EQUALS:{v1}")
except:
    pass

# Try original
try:
    Fernet(key.encode())
    print(f"VALID_ORIGINAL:{key}")
except:
    pass

# Generate new just in case
print(f"NEW_VALID_KEY:{Fernet.generate_key().decode()}")
