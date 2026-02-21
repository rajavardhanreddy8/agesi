import os, sys, re
from dotenv import load_dotenv

sys.path.insert(0, 'c:/Users/admin/Documents/outing/agent 4.0/form_filler')
load_dotenv()
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
sb = create_client(url, key)

res = sb.table('student_profiles').select('id, programme, specialization, full_name').execute()
for u in res.data:
    updates = {}
    if u['programme']:
        cleaned_prog = " ".join(str(u['programme']).split())
        if cleaned_prog != u['programme']:
            if cleaned_prog.startswith('CSE'):
                # They put specialization in programme
                updates['programme'] = 'B.Tech'
                if not u['specialization']:
                    updates['specialization'] = cleaned_prog
            else:
                updates['programme'] = cleaned_prog
    
    if u['specialization']:
        cleaned_spec = " ".join(str(u['specialization']).split())
        if cleaned_spec != u['specialization']:
            updates['specialization'] = cleaned_spec
            
    if u['full_name']:
        cleaned_name = " ".join(str(u['full_name']).split())
        if cleaned_name != u['full_name']:
            updates['full_name'] = cleaned_name
            
    if updates:
        sb.table('student_profiles').update(updates).eq('id', u['id']).execute()
        print(f"Fixed data for {u['full_name']}")
print("Cleanup complete")
