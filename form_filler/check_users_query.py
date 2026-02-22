import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

try:
    res1 = supabase.table('v_user_profiles').select('*').execute()
    with open('users_debug.json', 'w') as f:
        json.dump(res1.data, f, indent=2)
    print("Dumped to users_debug.json")
except Exception as e:
    print(f"Error fetching from view: {e}")
