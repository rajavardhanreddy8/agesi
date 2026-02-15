import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print(f"Checking schema for table 'users'...")

try:
    # Try to select the specific column to see if it exists
    # We limit to 1 row to be efficient
    response = supabase.table('users').select('verification_expires').limit(1).execute()
    print("SUCCESS: Column 'verification_expires' exists!")
    print(f"Data sample: {response.data}")
except Exception as e:
    print(f"ERROR: Could not access column. Details: {e}")
