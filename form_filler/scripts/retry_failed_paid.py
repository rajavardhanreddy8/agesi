import sys, json, uuid
from datetime import datetime
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras
import urllib.request

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get all PAID students who have a failed task today
# We'll use the latest failed task to reconstruct the form data
cur.execute("""
    SELECT DISTINCT ON (u.email)
           u.id as user_id, u.email, sh.form_url, sh.form_data, sub.plan_type
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    LEFT JOIN subscriptions sub ON u.id = sub.user_id
    WHERE sh.submitted_at > CURRENT_DATE
      AND sh.status = 'failed'
      AND (sub.plan_type != 'free' AND sub.plan_type IS NOT NULL)
    ORDER BY u.email, sh.submitted_at DESC
""")
failed_paid_users = cur.fetchall()

print(f"Found {len(failed_paid_users)} failed paid users to retry.")

cur_insert = conn.cursor()
inserted = 0

for user in failed_paid_users:
    # Use existing form_data if available, or fetch defaults if somehow missing
    form_data = user['form_data']
    if not form_data:
        print(f"Skipping {user['email']} - no form_data found.")
        continue
    
    if isinstance(form_data, str):
        form_data = json.loads(form_data)

    task_id = f"retry_paid_{user['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cur_insert.execute("""
        INSERT INTO submission_history 
            (user_id, form_url, task_id, leave_start_date, leave_end_date, status, form_data, submitted_at)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s, NOW())
    """, (
        user['user_id'], 
        user['form_url'], 
        task_id, 
        form_data.get('leave_start_date'), 
        form_data.get('leave_end_date'), 
        json.dumps(form_data)
    ))
    
    inserted += 1
    print(f"Re-queueing (Retry): {user['email']} (Plan: {user['plan_type']})")

conn.commit()
conn.close()

print(f"\nSuccessfully re-queued {inserted} retry tasks.")

if inserted > 0:
    print("Triggering reload HTTP endpoint...")
    req = urllib.request.Request("http://localhost:5000/api/admin/reload-pending", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print("Reload API response:", response.read().decode())
    except Exception as e:
        print("API Error:", e)
