import os, sys
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Clear ALL stuck queued/running entries older than 10 minutes
cur.execute("""
    UPDATE submission_history 
    SET status = 'failed', message = 'Cleared stuck queue entry'
    WHERE status IN ('queued', 'running') 
      AND submitted_at < NOW() - INTERVAL '10 minutes'
""")
print(f"Cleared {cur.rowcount} stuck entries")
conn.commit()
conn.close()
