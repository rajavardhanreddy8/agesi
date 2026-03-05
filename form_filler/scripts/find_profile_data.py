import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor()

# Check what tables exist
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

# Check if user_profiles exists
if 'user_profiles' in tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='user_profiles' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print("\nuser_profiles columns:", cols)

    cur2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur2.execute("SELECT * FROM user_profiles LIMIT 2")
    rows = cur2.fetchall()
    with open('profile_check.json', 'w') as f:
        json.dump([dict(r) for r in rows], f, indent=2, default=str)
    print("Saved to profile_check.json")
else:
    print("No 'user_profiles' table. Checking raw_user_meta_data...")
    cur2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur2.execute("SELECT id, email, raw_user_meta_data FROM users LIMIT 2")
    rows = cur2.fetchall()
    with open('profile_check.json', 'w') as f:
        json.dump([dict(r) for r in rows], f, indent=2, default=str)
    print("Saved raw_user_meta_data to profile_check.json")

conn.close()
