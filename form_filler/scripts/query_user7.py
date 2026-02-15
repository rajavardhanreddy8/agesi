"""Query User 7 profile"""
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Simple query

cur.execute("SELECT * FROM users WHERE id = 7")
row = cur.fetchone()

if row:
    cols = [desc[0] for desc in cur.description]
    print("=== USER 7 ===")
    for i, col in enumerate(cols):
        print(f"{col}: {row[i]}")
else:
    print("User 7 not found")

conn.close()
