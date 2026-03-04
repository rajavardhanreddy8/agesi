import os, sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
import psycopg2.extras
from db import get_db_connection
from auth_system_v2 import decrypt_outlook_password

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT sh.id, sh.user_id, sh.form_url, sh.leave_start_date, u.email, u.outlook_password_encrypted
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    WHERE sh.status = 'failed'
      AND sh.submitted_at > NOW() - INTERVAL '48 hours'
      AND sh.form_url NOT LIKE '%%dummy%%'
      AND sh.form_url NOT LIKE '%%example%%'
    ORDER BY sh.id DESC
""")
failed = cur.fetchall()

for f in failed:
    uid = f['user_id']
    sd = f['leave_start_date']
    email = f['email']
    
    # Check dup
    cur.execute("""
        SELECT id, status FROM submission_history 
        WHERE user_id = %s AND leave_start_date = %s AND status IN ('queued', 'running', 'completed')
    """, (uid, sd))
    dup = cur.fetchone()
    
    # Check password
    try:
        pw = decrypt_outlook_password(f['outlook_password_encrypted'])
        pw_ok = "OK"
    except Exception as e:
        pw_ok = f"FAIL: {e}"
    
    status = "BLOCKED-DUP" if dup else "READY"
    print(f"ID={f['id']} user={email} date={sd} dup={dup} pw={pw_ok} -> {status}")

conn.close()
