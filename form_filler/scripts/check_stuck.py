import sys
sys.path.insert(0, '.')
import psycopg2.extras
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Check all RUNNING tasks and how long they've been running
cur.execute("""
    SELECT 
        u.email,
        sh.id,
        sh.task_id,
        sh.status,
        sh.submitted_at,
        now() - sh.submitted_at AS running_for
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status = 'running'
    ORDER BY sh.submitted_at ASC
""")

running = cur.fetchall()
print(f"Stuck RUNNING tasks: {len(running)}")
for r in running:
    mins = int(r['running_for'].total_seconds() / 60) if r['running_for'] else '?'
    print(f"  {r['email']} | task={r['task_id']} | stuck {mins} min | at {r['submitted_at']}")

conn.close()
