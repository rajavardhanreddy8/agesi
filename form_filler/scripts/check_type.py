import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT form_data FROM submission_history WHERE status='running' OR status='failed' ORDER BY submitted_at DESC LIMIT 5")
rows = cur.fetchall()
for r in rows:
    fd = r['form_data']
    print(f"Type: {type(fd)}, Value: {repr(fd)}")

conn.close()
