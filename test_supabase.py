import sys
sys.path.insert(0, 'form_filler')
import os
from dotenv import load_dotenv

env_path = os.path.join('form_filler', '.env')
load_dotenv(dotenv_path=env_path, override=False)

import supabase as sb
# Force overide of URL / KEY if we can find them
sb_url = os.getenv("SUPABASE_URL")
sb_key = os.getenv("SUPABASE_KEY")
supabase = sb.create_client(sb_url, sb_key)

try:
    print("Testing correct query:")
    res = supabase.table('submission_history').select('task_id, status, users(email, student_profiles(full_name, roll_number))').limit(2).execute()
    print(res.data)
except Exception as e:
    print("Correct query failed:", e)

try:
    print("\nTesting old query:")
    res = supabase.table('submission_history').select('task_id, status, users(email), student_profiles(full_name, roll_number)').limit(2).execute()
    print(res.data)
except Exception as e:
    print("Old query failed:", e)
