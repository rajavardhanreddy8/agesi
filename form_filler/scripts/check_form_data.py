import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT sh.task_id, sh.status, u.email, 
           CASE WHEN sh.form_data IS NULL THEN 'NULL' ELSE 'EXISTS' END as has_form_data
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status='pending'
""")
rows = cur.fetchall()
print(f"Found {len(rows)} pending tasks:")
for r in rows:
    print(f"  {r['email']} | {r['status']} | form_data: {r['has_form_data']}")

conn.close()
