import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from auth_system_v2 import supabase

# check if any users exist that DON'T have a student_profile
users_res = supabase.table('users').select('id, email').execute()
profiles_res = supabase.table('student_profiles').select('user_id').execute()
subs_res = supabase.table('subscriptions').select('user_id').execute()

user_ids = {u['id'] for u in users_res.data}
profile_ids = {p['user_id'] for p in profiles_res.data}
sub_ids = {s['user_id'] for s in subs_res.data}

users_without_profile = user_ids - profile_ids
users_without_sub = user_ids - sub_ids

print(f"Total users: {len(user_ids)}")
print(f"Users with profiles: {len(profile_ids)}")
print(f"Users with subscriptions: {len(sub_ids)}")
print(f"Users WITHOUT profiles: {users_without_profile}")
print(f"Users WITHOUT subscriptions: {users_without_sub}")

# Show emails of users without profiles
if users_without_profile:
    for uid in users_without_profile:
        user = next(u for u in users_res.data if u['id'] == uid)
        print(f"  No profile: {user['email']}")

if users_without_sub:
    for uid in users_without_sub:
        user = next(u for u in users_res.data if u['id'] == uid)
        print(f"  No subscription: {user['email']}")
