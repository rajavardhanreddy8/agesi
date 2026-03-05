import sys
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Cancel the batch tasks that were created in error
cur.execute("UPDATE submission_history SET status='cancelled', message='Cancelled per user request - only paid and applied users should be submitted' WHERE task_id LIKE 'batch_%' AND status='pending'")
cancelled = cur.rowcount
conn.commit()
conn.close()

print(f"Cancelled {cancelled} batch tasks.")
