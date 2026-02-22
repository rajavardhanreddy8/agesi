import os, sys, json
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

res = supabase.table('submission_history').select('id, status, message').in_('status', ['running', 'queued']).execute()
print(f"Running or Queued tasks via Supabase: {len(res.data)}")
for r in res.data:
    print(r)
    
res2 = supabase.table('submission_history').select('id, status, message').in_('id', [126, 127]).execute()
print(f"Tasks 126, 127 via Supabase:")
for r in res2.data:
    print(r)
