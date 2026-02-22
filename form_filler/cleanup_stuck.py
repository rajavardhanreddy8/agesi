import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Mark stuck 'running' and 'queued' submissions as 'failed'
cur.execute("""
    UPDATE submission_history SET status = 'failed', 
    message = 'Cleaned up: Task was stuck due to invalid profile data (school=Unknown)'
    WHERE status IN ('running', 'queued')
""")
print(f"Cleaned up {cur.rowcount} stuck submissions")
conn.commit()
conn.close()
