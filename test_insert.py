
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_insert():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            sslmode='require'
        )
        cur = conn.cursor()
        
        # Test data
        user_id = 1
        form_url = "https://forms.office.com/r/test_link_123"
        start_date = "2026-02-14"
        end_date = "2026-02-16"
        
        # INSERT
        cur.execute("""
            INSERT INTO submission_history 
            (user_id, form_url, leave_start_date, leave_end_date, status, task_id, submitted_at)
            VALUES (%s, %s, %s, %s, 'test', 'manual_test', NOW())
        """, (user_id, form_url, start_date, end_date))
        
        conn.commit()
        conn.close()
        print("Test Insertion Successful!")
        
    except Exception as e:
        print(f"Test Insertion Failed: {e}")

if __name__ == "__main__":
    test_insert()
