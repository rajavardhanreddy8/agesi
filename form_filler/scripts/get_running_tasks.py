
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')

def get_running_tasks():
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
        
        # Get tasks that are currently 'running'
        cur.execute("SELECT task_id, status, submitted_at, error_details FROM submission_history WHERE status = 'running' ORDER BY submitted_at DESC")
        tasks = cur.fetchall()
        
        if not tasks:
            print("No tasks are currently running.")
        else:
            print(f"Found {len(tasks)} running tasks:")
            for task in tasks:
                task_id, status, submitted_at, error = task
                if submitted_at and submitted_at.tzinfo is None:
                    # If DB returns naive, assume UTC from Postgres
                    submitted_at = submitted_at.replace(tzinfo=pytz.UTC)

                # Convert to IST for display
                if submitted_at:
                    submitted_at_ist = submitted_at.astimezone(IST)
                else:
                    submitted_at_ist = None

                now = datetime.now(IST)
                duration = now - submitted_at_ist if submitted_at_ist else None
                print(f"ID: {task_id} | Status: {status} | Started (IST): {submitted_at_ist} | Duration: {duration}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    get_running_tasks()
