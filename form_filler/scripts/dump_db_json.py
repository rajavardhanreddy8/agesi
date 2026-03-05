import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras
from datetime import datetime

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT sh.status, sh.message, sh.submitted_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' as ist_time, u.email
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.submitted_at > CURRENT_DATE
    ORDER BY sh.submitted_at DESC
""")

rows = cur.fetchall()
# convert datetime to string for json serialization
for r in rows:
    if r['ist_time']:
        r['ist_time'] = r['ist_time'].strftime("%Y-%m-%d %H:%M:%S")

with open('recent_status.json', 'w') as f:
    json.dump([dict(r) for r in rows], f, indent=2)

print("Saved to recent_status.json")
conn.close()
