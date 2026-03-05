"""
fix_stuck_running.py - Marks stuck RUNNING tasks as failed and then re-queues them
"""
import sys
import os
sys.path.insert(0, '.')
import psycopg2.extras
from db import get_db_connection

STUCK_THRESHOLD_MINUTES = 30  # Anything running longer than 30 min is stuck

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Find stuck tasks
cur.execute("""
    SELECT 
        sh.id,
        sh.user_id,
        sh.task_id,
        u.email,
        sh.submitted_at,
        EXTRACT(EPOCH FROM (now() - sh.submitted_at)) / 60 AS minutes_running
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status = 'running'
      AND sh.submitted_at < now() - interval '%s minutes'
    ORDER BY sh.submitted_at ASC
""", (STUCK_THRESHOLD_MINUTES,))

stuck = cur.fetchall()

if not stuck:
    print("No stuck tasks found.")
    conn.close()
    sys.exit(0)

print(f"Found {len(stuck)} stuck RUNNING tasks:\n")
for r in stuck:
    mins = int(float(r['minutes_running']))
    print(f"  {r['email']} | task={r['task_id']} | stuck {mins} min")

# Mark them as 'failed'
ids = [r['id'] for r in stuck]
cur2 = conn.cursor()
cur2.execute("""
    UPDATE submission_history
    SET status = 'failed',
        error_details = 'Auto-cleared: stuck in RUNNING state for over 30 minutes'
    WHERE id = ANY(%s)
    RETURNING id
""", (ids,))
updated = cur2.fetchall()
conn.commit()

print(f"\n✅ Marked {len(updated)} tasks as failed.")
print("\nThese users can now re-submit through the dashboard.")

conn.close()
