"""
Fix stuck queue: update 'queued' tasks to 'pending' so the worker's recover_pending_tasks
picks them up on next cycle. Then trigger recovery via API.
"""
import sys, requests
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1. Show current queued tasks
cur.execute("""
    SELECT sh.task_id, sh.status, sh.leave_start_date, u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status = 'queued'
    ORDER BY sh.submitted_at
""")
queued = cur.fetchall()
print(f"Queued tasks: {len(queued)}")
for q in queued:
    print(f"  {q['email']} | {q['leave_start_date']} | {q['task_id']}")

if queued:
    # 2. Update status from 'queued' to 'pending' so recover_pending_tasks picks them up
    cur.execute("""
        UPDATE submission_history
        SET status = 'pending'
        WHERE status = 'queued'
        RETURNING task_id
    """)
    updated = cur.fetchall()
    conn.commit()
    print(f"\n✅ Updated {len(updated)} tasks from 'queued' to 'pending'")

conn.close()

# 3. Hit the recovery endpoint to re-load them into the in-memory queue
try:
    r = requests.post('http://localhost:5000/api/admin/recover-stuck-tasks', timeout=10)
    print(f"\nRecovery API response: {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"\nRecovery API call failed: {e}")
    print("(Worker will pick them up automatically on next idle cycle)")

print("\nDone. Tasks should now be processing.")
