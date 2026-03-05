import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get today's paid users who are not cancelled by the restart script
cur.execute("""
    SELECT DISTINCT ON (u.email)
           u.email, sh.status, sh.message, sub.plan_type
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.submitted_at > CURRENT_DATE
      AND (sub.plan_type != 'free' AND sub.plan_type IS NOT NULL)
      AND sh.status != 'cancelled'
    ORDER BY u.email, sh.submitted_at DESC
""")
rows = cur.fetchall()

print("TODAY'S PAID STATUS REPORT:")
rem_count = 0
for r in rows:
    msg = (r['message'] or 'No message').strip()
    print(f"- {r['email']} ({r['plan_type']}): [{r['status'].upper()}] {msg}")
    if r['status'] in ('pending', 'running'):
        rem_count += 1

print(f"\nREMAINING PAID TASKS: {rem_count}")
conn.close()
