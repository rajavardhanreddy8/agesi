import os
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

def inspect_queue():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT count(*) as cnt FROM submission_history")
        print(f"Total rows: {cur.fetchone()['cnt']}", flush=True)

        print("Fetching last 10 tasks...", flush=True)
        cur.execute("SELECT id, task_id, status, submitted_at FROM submission_history ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        
        for row in rows:
            print(f"Task: {row['task_id']} | Status: {row['status']} | Msg: {row.get('message')}", flush=True)
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_queue()
