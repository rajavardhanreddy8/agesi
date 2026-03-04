"""Check current queued tasks after requeue"""
import json, sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("""
    SELECT sh.task_id, sh.status, sh.leave_start_date, sh.leave_end_date, u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id 
    WHERE sh.status IN ('queued', 'running')
    ORDER BY sh.submitted_at DESC
""")
rows = cur.fetchall()
print(f"Currently queued/running: {len(rows)}")
for r in rows:
    print(f"  {r['email']} | {r['leave_start_date']} -> {r['leave_end_date']} | {r['status']}")
conn.close()
