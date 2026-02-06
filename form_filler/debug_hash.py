
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from supabase import create_client, Client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Get the user's password hash from the database
email = "guntaka.reddy_2028@woxsen.edu.in"
result = supabase.table('users').select('id, email, password_hash').eq('email', email).execute()

if result.data:
    user = result.data[0]
    print(f"User ID: {user['id']}")
    print(f"Email: {user['email']}")
    print(f"Password Hash: {user['password_hash']}")
    print(f"Hash Length: {len(user['password_hash'])}")
    print(f"Hash Starts With $2b$: {user['password_hash'].startswith('$2b$')}")
else:
    print("User not found!")
