import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

def check():
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("SELECT id, task_id, status, user_id, message, form_url, form_data FROM submission_history WHERE task_id = 'task_7_20260215_105950'")
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} tasks:")
    for row in rows:
        print(f"Task {row['task_id']}:")
        print(f"  Status: {row['status']}")
        print(f"  Message: {row['message']}")
        if row.get('form_data'):
            print(f"  Has FormData: Yes")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
