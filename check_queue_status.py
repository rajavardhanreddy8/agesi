
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def check_queue():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n--- Latest 5 entries in submission_history ---")
        cur.execute("SELECT id, status, submitted_at, task_id FROM submission_history ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(f"ID: {row['id']} | Status: {row['status']} | TaskID: {row['task_id']} | Date: {row['submitted_at']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_queue()
