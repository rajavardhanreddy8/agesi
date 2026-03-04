"""
Resubmit all failed submissions from the latest batch.
Queries DB for failed submissions, then re-queues them via the /api/submit-form endpoint logic.
"""
import os, sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Find all failed submissions from the latest batch (today)
cur.execute("""
    SELECT sh.id, sh.user_id, sh.form_url, sh.task_id, sh.leave_start_date, sh.leave_end_date, sh.status, sh.message,
           u.email, sp.full_name, sp.roll_number
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    LEFT JOIN student_profiles sp ON sp.user_id = sh.user_id
    WHERE sh.status = 'failed'
      AND sh.submitted_at > NOW() - INTERVAL '24 hours'
    ORDER BY sh.id DESC
""")

failed = cur.fetchall()
print(f"\n{'='*60}")
print(f"Found {len(failed)} failed submissions in the last 24 hours:")
print(f"{'='*60}")

for f in failed:
    print(f"\n  ID: {f['id']}")
    print(f"  User: {f['email']} (ID: {f['user_id']})")
    print(f"  Name: {f.get('full_name', 'N/A')}")
    print(f"  Task: {f['task_id']}")
    print(f"  Dates: {f['leave_start_date']} to {f['leave_end_date']}")
    print(f"  Error: {f['message'][:100] if f['message'] else 'N/A'}")

print(f"\n{'='*60}")
conn.close()
