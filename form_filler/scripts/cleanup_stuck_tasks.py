
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')

def cleanup_stuck_tasks():
    load_dotenv()
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        # Mark tasks that have been 'running' for more than 30 minutes as failed
        query = "UPDATE submission_history SET status = 'failed', error_details = 'Timeout: Automation took too long or was interrupted' WHERE status = 'running' AND submitted_at < NOW() - INTERVAL '30 minutes'"
        cur.execute(query)
        
        rowcount = cur.rowcount
        conn.commit()
        now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
        print(f"✅ [{now_ist}] Cleared {rowcount} stuck tasks (running >30 min).")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")

if __name__ == "__main__":
    cleanup_stuck_tasks()
