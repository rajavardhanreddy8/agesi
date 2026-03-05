import sys, requests
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Set all failed and queued from today back to pending
cur.execute("""
    UPDATE submission_history 
    SET status='pending', error_details=NULL 
    WHERE submitted_at > CURRENT_DATE 
    AND status IN ('queued', 'failed')
""")
print(f"Updated {cur.rowcount} tasks to 'pending'")

conn.commit()
conn.close()

# Trigger reload
try:
    r = requests.post('http://localhost:5000/api/admin/reload-pending', timeout=10)
    print(f"\nReload API response: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"\nAPI trigger failed: {e}")
