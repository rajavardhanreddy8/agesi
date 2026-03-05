import sys
import psycopg2.extras
sys.path.insert(0, '.')
from db import get_db_connection

conn=get_db_connection()
cur=conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT email, status, message 
    FROM submission_history sh 
    JOIN users u ON sh.user_id = u.id 
    WHERE task_id LIKE 'retry_paid_%' 
    ORDER BY submitted_at DESC
""")
rows = cur.fetchall()

print(f"\nSTATUS OF {len(rows)} RETRIES:")
success_count = 0
for row in rows:
    status = row['status'].upper()
    print(f"[{status}] {row['email']}: {row['message']}")
    if status == 'COMPLETED':
        success_count += 1

print(f"Total Successful: {success_count}/{len(rows)}")
conn.close()
