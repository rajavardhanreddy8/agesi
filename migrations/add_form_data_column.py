import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

def migrate():
    try:
        # Connect to DB
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )
        cur = conn.cursor()
        
        # Add form_data column if not exists
        print("Adding form_data column to submission_history...")
        cur.execute("""
            ALTER TABLE submission_history 
            ADD COLUMN IF NOT EXISTS form_data JSONB,
            ADD COLUMN IF NOT EXISTS blob_name TEXT;
        """)
        
        conn.commit()
        print("Migration successful!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
