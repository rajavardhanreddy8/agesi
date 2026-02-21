import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
sb = create_client(url, key)

# Find all test users
res = sb.table('users').select('id, email').execute()
test_users = [
    u for u in res.data
    if u['email'].startswith('test_')
    or u['email'].startswith('debug_user')
    or u['email'].startswith('verify_fix')
    or u['email'].startswith('agent_verify')
    or u['email'].startswith('test_connection')
    or u['email'].startswith('test_timestamp')
]

print("Found {} test users to delete:".format(len(test_users)))
for u in test_users:
    print("  - {} (id={})".format(u['email'], u['id']))

# Delete them one by one (CASCADE will clean up related tables)
deleted = 0
for u in test_users:
    try:
        sb.table('users').delete().eq('id', u['id']).execute()
        print("  DELETED: {}".format(u['email']))
        deleted += 1
    except Exception as e:
        print("  FAILED to delete {}: {}".format(u['email'], str(e)))

print("\nDone! Deleted {}/{} test users.".format(deleted, len(test_users)))
