import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1. First, mark Avinash's latest tasks as completed (manually done)
cur.execute("""
    UPDATE submission_history 
    SET status = 'completed', message = 'User manually submitted form'
    WHERE user_id IN (SELECT id FROM users WHERE email = 'avinash.kumar_2028@woxsen.edu.in')
      AND submitted_at > CURRENT_DATE
      AND status IN ('pending', 'running', 'failed')
""")
print(f"Updated {cur.rowcount} tasks for Avinash to COMPLETED.")
conn.commit()

# 2. Now show REMAINING tasks for today (only paid)
cur.execute("""
    SELECT DISTINCT ON (u.email)
           sh.status, u.email, sub.plan_type, sh.task_id
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.submitted_at > CURRENT_DATE
      AND (sub.plan_type != 'free' AND sub.plan_type IS NOT NULL)
    ORDER BY u.email, sh.submitted_at DESC
""")
rows = cur.fetchall()

print("\n--- STATUS OF TODAY'S PAID APPLICATIONS ---")
for r in rows:
    print(f"[{r['status'].upper()}] {r['email']} (Plan: {r['plan_type']})")

# 3. Specifically count what is "remaining" (pending/running)
cur.execute("""
    SELECT COUNT(*) 
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.submitted_at > CURRENT_DATE
      AND sh.status IN ('pending', 'running')
      AND (sub.plan_type != 'free' AND sub.plan_type IS NOT NULL)
""")
remain_count = cur.fetchone()['count']
print(f"\nREMAINING PAID TASKS TO PROCESS: {remain_count}")

conn.close()
