
import json
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# File path
JSON_PATH = r"c:\Users\admin\Documents\outing\agent 4.0\doc_handle\public\outing_data.json"

def migrate_json_to_db():
    try:
        # Read JSON
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
            
        form_link = data.get('form_link')
        start_str = data.get('start_date') # DD.MM.YYYY
        end_str = data.get('end_date')     # DD.MM.YYYY
        
        # Parse Dates
        start_date = datetime.strptime(start_str, "%d.%m.%Y").date()
        end_date = datetime.strptime(end_str, "%d.%m.%Y").date()
        
        print(f"Migrating: {form_link}, {start_date} to {end_date}")
        
        # Connect to DB
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            sslmode='require'
        )
        cur = conn.cursor()
        
        # Check if already exists? (Optional, but let's just insert newest)
        # We insert a dummy record with user_id=0 (system) or just null if allowed?
        # Typically user_id is NOT NULL. I'll use a valid user_id if possible, or 1.
        # Let's check a valid user_id first.
        cur.execute("SELECT id FROM users LIMIT 1")
        user = cur.fetchone()
        user_id = user[0] if user else 1 # Fallback to 1
        
        # INSERT
        cur.execute("""
            INSERT INTO submission_history 
            (user_id, form_url, leave_start_date, leave_end_date, status, task_id, submitted_at)
            VALUES (%s, %s, %s, %s, 'migrated', 'json_migration', NOW())
        """, (user_id, form_link, start_date, end_date))
        
        conn.commit()
        conn.close()
        print("Migration Successful!")
        
    except Exception as e:
        print(f"Migration Failed: {e}")

if __name__ == "__main__":
    migrate_json_to_db()
