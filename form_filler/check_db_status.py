import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT id, status, message FROM submission_history WHERE id IN (126, 127)")
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
