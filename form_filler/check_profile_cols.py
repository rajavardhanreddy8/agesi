import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

# Get columns from student_profiles via a single row
try:
    res = supabase.table('student_profiles').select('*').limit(1).execute()
    if res.data:
        cols = list(res.data[0].keys())
        for c in cols:
            print(c)
    else:
        print("No rows in student_profiles")
except Exception as e:
    print(f"Error: {e}")
