import sys
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Check subscriptions columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='subscriptions'")
print("subscriptions columns:", [r[0] for r in cur.fetchall()])

# Check users columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
print("users columns:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT email, plan_type FROM users WHERE email ILIKE '%guntaka%'")
users = cur.fetchall()
print("user plan_type:", users)

cur.close()
conn.close()
