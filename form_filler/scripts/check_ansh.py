import sys
sys.path.insert(0, '.')
import psycopg2.extras
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT sh.status, sh.task_id, sh.submitted_at, sh.error_details, sh.completed_at
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE u.email LIKE '%ansh.dhingra%'
    ORDER BY sh.submitted_at DESC
    LIMIT 10
""")

rows = cur.fetchall()
if not rows:
    print("No submissions found for Ansh Dhingra")
else:
    print(f"Submission history for Ansh Dhingra ({len(rows)} records):")
    for r in rows:
        print(f"  status={r['status']} | submitted={r['submitted_at']} | completed={r['completed_at']}")
        if r['error_details']:
            print(f"    error: {r['error_details']}")

conn.close()
