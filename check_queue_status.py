import psycopg2.extras
from form_filler.db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT task_id, status, error_details FROM submission_history WHERE leave_start_date = '04-10-2026' ORDER BY id DESC")
rows = cur.fetchall()
print(f"Total tasks: {len(rows)}")
for r in rows:
    err = (r['error_details'] or '')[:80]
    print(f"  {r['task_id']}: {r['status']}  {err}")
conn.close()
