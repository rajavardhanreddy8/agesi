import logging
logging.basicConfig(level=logging.ERROR)
import traceback
from db import get_db_connection
import supabase
import os
from dotenv import load_dotenv

load_dotenv()
sb = supabase.create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

try:
    res = sb.table('submission_history').select('task_id, status, message, error_details, leave_start_date, leave_end_date, screenshot_path, submitted_at, users(email, student_profiles(full_name, roll_number))').order('submitted_at', desc=True).limit(5).execute()
    print("Success")
except Exception as e:
    print(traceback.format_exc())
