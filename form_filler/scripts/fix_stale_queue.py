"""
Remove queued tasks with old dates (2026-02-13) and re-queue with correct dates (2026-03-06 -> 2026-03-08).
"""
import sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1. Find all queued tasks with old dates
cur.execute("""
    SELECT sh.id, sh.task_id, sh.user_id, sh.leave_start_date, sh.leave_end_date, u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status = 'queued' AND sh.leave_start_date = '2026-02-13'
""")
old_tasks = cur.fetchall()
print(f"Found {len(old_tasks)} queued tasks with old date 2026-02-13:")
for t in old_tasks:
    print(f"  {t['email']} | {t['task_id']} | {t['leave_start_date']} -> {t['leave_end_date']}")

# 2. Delete them
if old_tasks:
    task_ids = [t['task_id'] for t in old_tasks]
    cur.execute("DELETE FROM submission_history WHERE task_id = ANY(%s)", (task_ids,))
    conn.commit()
    print(f"\n✅ Deleted {cur.rowcount} old queued tasks")
else:
    print("No old tasks to delete")

conn.close()
print("Done.")
