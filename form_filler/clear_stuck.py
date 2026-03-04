"""
Check for stuck queued submissions and mark them as failed so they can be retried.
Then list what's eligible for resubmission.
"""
import os, sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
import psycopg2.extras
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Find stuck queued/running submissions (older than 30 minutes)
cur.execute("""
    SELECT sh.id, sh.user_id, sh.task_id, sh.status, sh.leave_start_date, sh.submitted_at, u.email
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    WHERE sh.status IN ('queued', 'running')
      AND sh.submitted_at < NOW() - INTERVAL '30 minutes'
    ORDER BY sh.id DESC
""")
stuck = cur.fetchall()
print(f"Found {len(stuck)} stuck queued/running submissions:")
for s in stuck:
    print(f"  ID={s['id']} task={s['task_id']} user={s['email']} status={s['status']} date={s['leave_start_date']} at={s['submitted_at']}")

if stuck:
    # Mark them as failed so they can be retried
    ids = [s['id'] for s in stuck]
    cur.execute("""
        UPDATE submission_history 
        SET status = 'failed', message = 'Marked failed: was stuck in queued/running state'
        WHERE id = ANY(%s)
    """, (ids,))
    conn.commit()
    print(f"\nMarked {len(ids)} stuck submissions as failed.")

# Now show what's eligible for retry
cur.execute("""
    SELECT sh.id, sh.user_id, sh.form_url, sh.leave_start_date, sh.leave_end_date, u.email, sh.message
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    WHERE sh.status = 'failed'
      AND sh.submitted_at > NOW() - INTERVAL '48 hours'
      AND sh.form_url NOT LIKE '%%dummy%%'
      AND sh.form_url NOT LIKE '%%example%%'
    ORDER BY sh.id DESC
""")
eligible = cur.fetchall()
print(f"\n{len(eligible)} failed submissions now eligible for retry:")
for e in eligible:
    # Check for duplicates
    cur.execute("""
        SELECT 1 FROM submission_history 
        WHERE user_id = %s AND leave_start_date = %s AND status IN ('queued', 'running', 'completed')
    """, (e['user_id'], e['leave_start_date']))
    dup = cur.fetchone()
    marker = "BLOCKED (dup)" if dup else "READY"
    print(f"  [{marker}] ID={e['id']} {e['email']} {e['leave_start_date']}->{e['leave_end_date']}")

conn.close()
