import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Check all paid users for today
cur.execute("""
    SELECT u.email, sh.status, sh.message, sh.submitted_at
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.submitted_at > CURRENT_DATE
      AND (sub.plan_type != 'free' AND sub.plan_type IS NOT NULL)
    ORDER BY sh.submitted_at DESC
""")
all_paid = cur.fetchall()

print("--- TODAY'S PAID USER STATUS ---")
for r in all_paid:
    print(f"- {r['email']}: [{r['status'].upper()}] {r['message']}")

conn.close()
