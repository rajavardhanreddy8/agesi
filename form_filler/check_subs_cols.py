import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

res = supabase.table('subscriptions').select('*').limit(2).execute()
if res.data:
    print("subscriptions columns:", list(res.data[0].keys()))
    print("sample:", res.data[0])
