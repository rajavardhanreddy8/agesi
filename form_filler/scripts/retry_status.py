import sys
import psycopg2.extras
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT DISTINCT ON (u.email) 
           u.email, sh.status, sh.message
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.task_id LIKE 'retry_paid_%'
    ORDER BY u.email, sh.submitted_at DESC
""")

for r in cur.fetchall():
    status = r['status'].upper()
    email = r['email']
    msg = (r['message'] or '')[:90]
    print(f"{status} | {email} | {msg}")

conn.close()
