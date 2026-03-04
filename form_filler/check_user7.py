import os,sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
import psycopg2.extras
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Show all submissions for user 7 on 2026-03-03
cur.execute("""
    SELECT id, task_id, status, leave_start_date, submitted_at, message 
    FROM submission_history 
    WHERE user_id=7 AND leave_start_date='2026-03-03' 
    ORDER BY id DESC
""")
rows = cur.fetchall()
print(f"User 7 submissions for 2026-03-03: {len(rows)}")
for r in rows:
    print(f"  ID={r['id']} task={r['task_id']} status={r['status']} msg={str(r.get('message',''))[:80]}")

# Show ALL stuck queued/running for any user
cur.execute("""
    SELECT sh.id, sh.user_id, sh.task_id, sh.status, sh.leave_start_date, u.email
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    WHERE sh.status IN ('queued', 'running')
    ORDER BY sh.id DESC
""")
stuck = cur.fetchall()
print(f"\nAll queued/running entries: {len(stuck)}")
for s in stuck:
    print(f"  ID={s['id']} user={s['email']} status={s['status']} date={s['leave_start_date']}")

conn.close()
