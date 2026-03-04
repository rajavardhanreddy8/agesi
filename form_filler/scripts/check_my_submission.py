import json, sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("""
    SELECT sh.task_id, sh.status, sh.message, sh.leave_start_date, sh.leave_end_date, sh.submitted_at, u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    ORDER BY sh.submitted_at DESC
    LIMIT 10
""")
rows = cur.fetchall()
with open('my_submissions.json', 'w') as f:
    json.dump([{k: str(v) for k, v in dict(r).items()} for r in rows], f, indent=2)
print(f"Wrote {len(rows)} records to my_submissions.json")
conn.close()
