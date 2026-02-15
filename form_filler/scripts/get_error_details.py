
import psycopg2
import os
from dotenv import load_dotenv

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
    
    # Get the most recent failed task
    cur.execute("""
        SELECT task_id, status, error_details, submitted_at, form_url, pdf_path
        FROM submission_history 
        WHERE status = 'failed'
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    row = cur.fetchone()
    if row:
        print(f"Task ID: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"Error: {row[2]}")
        print(f"Time: {row[3]}")
        print(f"Form URL: {row[4]}")
        print(f"PDF Path: {row[5]}")
    else:
        print("No failed tasks found.")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
