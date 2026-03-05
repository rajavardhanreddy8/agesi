import sys
import psycopg2.extras
sys.path.insert(0, '.')
from db import get_db_connection
from collections import defaultdict

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT DISTINCT ON (u.email)
           u.email, sh.status, LEFT(sh.message, 80) as short_msg
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.task_id LIKE 'retry_paid_%'
    ORDER BY u.email, sh.submitted_at DESC
""")
rows = cur.fetchall()

print(f"RETRY SUMMARY FOR {len(rows)} USERS:")
grouped = defaultdict(list)
for r in rows:
    msg = (r['short_msg'] or '').strip()
    key = 'COMPLETED' if r['status'] == 'completed' else msg[:60]
    grouped[key].append(r['email'])

for key, emails in sorted(grouped.items()):
    print(f"\n[{key}]")
    for e in emails:
        print(f"  {e}")

conn.close()
