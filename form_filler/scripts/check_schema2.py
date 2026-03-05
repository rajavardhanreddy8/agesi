import sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("Users columns:", ", ".join(cols))

cur2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur2.execute("SELECT * FROM users LIMIT 2")
rows = cur2.fetchall()
for r in rows:
    print(dict(r))
conn.close()
