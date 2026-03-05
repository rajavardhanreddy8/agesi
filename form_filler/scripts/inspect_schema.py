import sys
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
print("users table columns:", cur.fetchall())

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='subscriptions'")
print("subscriptions table columns:", cur.fetchall())

conn.commit()
cur.close()
conn.close()
