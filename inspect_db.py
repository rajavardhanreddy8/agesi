
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Error: {e}")
        return None

conn = get_db_connection()
if conn:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("--- Querying submission_history (Last 5) ---")
    cur.execute("SELECT id, form_url, leave_start_date, status, submitted_at FROM submission_history ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    
    if not rows:
        print("No rows found in submission_history.")
    else:
        for row in rows:
            print(f"ID: {row['id']}, Date: {row['leave_start_date']}, URL: {row['form_url']}, Status: {row['status']}")
            
    # Check count where form_url is not null
    cur.execute("SELECT COUNT(*) as count FROM submission_history WHERE form_url IS NOT NULL AND form_url != ''")
    count = cur.fetchone()['count']
    print(f"\nTotal rows with valid form_url: {count}")
    
    conn.close()
