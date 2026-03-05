import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT sh.status, sh.message, u.email 
    FROM submission_history sh 
    JOIN users u ON sh.user_id = u.id 
    WHERE sh.status='failed' AND sh.submitted_at > CURRENT_DATE
    ORDER BY sh.submitted_at DESC
""")
rows = cur.fetchall()
print(f"Found {len(rows)} failed tasks today:")
for r in rows:
    print(f"  {r['email']} | {r['message']}")

conn.close()
