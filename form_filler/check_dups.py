import os, sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
import psycopg2.extras
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Find failed submissions
cur.execute("""
    SELECT sh.id, sh.user_id, sh.form_url, sh.leave_start_date, sh.leave_end_date, u.email
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    WHERE sh.status = 'failed'
      AND sh.submitted_at > NOW() - INTERVAL '48 hours'
      AND sh.form_url NOT LIKE '%%dummy%%'
      AND sh.form_url NOT LIKE '%%example%%'
    ORDER BY sh.id DESC
""")
failed = cur.fetchall()
print(f"FAILED COUNT: {len(failed)}")

for f in failed:
    uid = f['user_id']
    sd = f['leave_start_date']
    # Check if already has completed/queued
    cur.execute("""
        SELECT status FROM submission_history 
        WHERE user_id = %s AND leave_start_date = %s AND status IN ('queued', 'running', 'completed')
    """, (uid, sd))
    dup = cur.fetchone()
    print(f"  ID={f['id']} user={f['email']} date={sd} dup={dup}")

conn.close()
