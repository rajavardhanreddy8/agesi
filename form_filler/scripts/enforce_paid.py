import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()

# Find pending/running tasks for users on the 'free' plan
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("""
    SELECT sh.task_id, u.email, sub.plan_type
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.status IN ('pending', 'running')
      AND (sub.plan_type = 'free' OR sub.plan_type IS NULL)
""")
free_tasks = cur.fetchall()

if free_tasks:
    task_ids = [t['task_id'] for t in free_tasks]
    print(f"Found {len(task_ids)} tasks belonging to free users. Canceling...")
    
    cur_update = conn.cursor()
    cur_update.execute("""
        UPDATE submission_history 
        SET status = 'cancelled', message = 'Cancelled - Free plan users exceeded limit or non-paid users cannot use auto-submit.'
        WHERE task_id = ANY(%s)
    """, (task_ids,))
    conn.commit()
    print(f"Cancelled {cur_update.rowcount} free tasks.")
else:
    print("No free/unpaid tasks found in the queue. All remaining tasks are for paid users.")

# Show remaining tasks
cur.execute("""
    SELECT sh.task_id, sh.status, u.email, sub.plan_type
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.status IN ('pending', 'running', 'completed')
      AND sh.submitted_at > CURRENT_DATE
    ORDER BY sh.status
""")
remaining = cur.fetchall()
print("\nTODAY'S TASK STATUS:")
for r in remaining:
    print(f"[{r['status'].upper()}] {r['email']} (Plan: {r['plan_type']}) - {r['task_id']}")

conn.close()
