import sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT status, COUNT(*) as count 
    FROM submission_history 
    WHERE submitted_at > CURRENT_DATE
    GROUP BY status
""")
stats = cur.fetchall()
print("=== TODAY'S OVERALL STATUS ===")
for row in stats:
    print(f"- {row['status']}: {row['count']} tasks")

cur.execute("""
    SELECT sh.status, u.email, sub.plan_type
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.submitted_at > CURRENT_DATE
      AND sh.status IN ('pending', 'running', 'completed')
    ORDER BY sh.status
""")
active = cur.fetchall()
print("\n=== ACTIVE TASKS (Paid & Applied) ===")
for r in active:
    print(f"[{r['status'].upper()}] {r['email']} | Plan: {r['plan_type']}")

conn.close()
