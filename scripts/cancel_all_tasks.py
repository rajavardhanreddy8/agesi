import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to find .env
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

def cancel_all_tasks():
    try:
        print("Connecting to database...", flush=True)
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )
        cur = conn.cursor()
        
        # Update pending and running tasks to 'cancelled'
        print("Cancelling all 'pending' and 'running' tasks...", flush=True)
        cur.execute("""
            UPDATE submission_history 
            SET status = 'cancelled', message = 'Cancelled by user request'
            WHERE status IN ('pending', 'running')
        """)
        
        rows_affected = cur.rowcount
        conn.commit()
        
        print(f"SUCCESS: Cancelled {rows_affected} tasks.", flush=True)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: Failed to cancel tasks: {e}", flush=True)

if __name__ == "__main__":
    cancel_all_tasks()
