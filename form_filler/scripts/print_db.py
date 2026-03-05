import sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

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
for r in rows:
    time_str = r['ist_time'].strftime("%I:%M %p") if r['ist_time'] else "N/A"
    print(f"{time_str} | {r['status']:<10} | {r['email']:<30} | {r['message']}")

conn.close()
