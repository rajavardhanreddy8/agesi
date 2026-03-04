import os, sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
import psycopg2.extras
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Show latest submissions with retry prefix
cur.execute("""
    SELECT sh.id, sh.task_id, sh.status, sh.leave_start_date, sh.submitted_at, u.email, sh.message
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    WHERE sh.task_id LIKE 'retry_%%'
    ORDER BY sh.id DESC
""")
retries = cur.fetchall()
print(f"Retry submissions: {len(retries)}")
for r in retries:
    msg = str(r.get('message', ''))[:60]
    print(f"  ID={r['id']} {r['email'][:30]} status={r['status']} task={r['task_id']} msg={msg}")

# Summary of all recent submissions
cur.execute("""
    SELECT sh.status, COUNT(*) as cnt
    FROM submission_history sh
    WHERE sh.submitted_at > NOW() - INTERVAL '48 hours'
    GROUP BY sh.status
""")
summary = cur.fetchall()
print(f"\nAll submissions last 48h:")
for s in summary:
    print(f"  {s['status']}: {s['cnt']}")

conn.close()
