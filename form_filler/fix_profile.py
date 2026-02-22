import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

# Fix guntaka.reddy's profile - user_id = 7
res = supabase.table('student_profiles').update({
    'school': 'School of Technology',
    'academic_year': '2024-2028'
}).eq('user_id', 7).execute()

print(f"Updated {len(res.data)} row(s)")
if res.data:
    print(f"  school: {res.data[0].get('school')}")
    print(f"  academic_year: {res.data[0].get('academic_year')}")
