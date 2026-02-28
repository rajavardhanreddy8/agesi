"""Quick script to check failed submission details for the 2 users."""
from form_filler.db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT sh.task_id, sh.status, sh.error_details, sh.message, 
           sh.submitted_at, sh.leave_start_date, u.email
    FROM submission_history sh 
    JOIN users u ON sh.user_id = u.id 
    WHERE u.email IN ('bhuvanachandra.k_2028@woxsen.edu.in', 'sunhith.kande_2028@woxsen.edu.in') 
    ORDER BY sh.submitted_at DESC 
    LIMIT 10
""")

rows = cur.fetchall()
if not rows:
    print("No submission records found for these users.")
else:
    for r in rows:
        print("=" * 60)
        print(f"Email:      {r['email']}")
        print(f"Status:     {r['status']}")
        print(f"Error:      {r.get('error_details', 'N/A')}")
        print(f"Message:    {r.get('message', 'N/A')}")
        print(f"Submitted:  {r.get('submitted_at', 'N/A')}")
        print(f"Start Date: {r.get('leave_start_date', 'N/A')}")
        print(f"Task ID:    {r['task_id']}")

conn.close()
