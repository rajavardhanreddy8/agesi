import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT u.email, sh.form_data 
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status='failed' AND sh.message LIKE '%roll_number%' 
    ORDER BY sh.submitted_at DESC LIMIT 3
""")
rows = cur.fetchall()
print(json.dumps([dict(r) for r in rows], indent=2))
conn.close()
