import sys
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("Users table columns:")
for c in cols:
    print(f"  - {c}")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='submission_history' ORDER BY ordinal_position")
print("\nSubmission history columns:")
for c in [r[0] for r in cur.fetchall()]:
    print(f"  - {c}")

conn.close()
