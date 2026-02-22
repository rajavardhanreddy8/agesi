import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

try:
    res1 = supabase.table('users').select('id, email').execute()
    print(f"Table 'users' returned {len(res1.data)} users")
    with open('users_table_debug.json', 'w') as f:
        json.dump(res1.data, f, indent=2)
except Exception as e:
    print(f"Error fetching from table: {e}")
