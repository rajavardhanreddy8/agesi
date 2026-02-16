
import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Setup paths (same as db.py)
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path, override=False)

def create_config_table():
    try:
        # Connection logic mirroring db.py
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER', 'postgres.uehkqlamchtdzcusqmhi') # Fallback from db.py
        db_password = os.getenv('DB_PASSWORD')
        db_port = os.getenv('DB_PORT', 5432)
        
        print(f"Connecting to {db_host} as {db_user}...")
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
            connect_timeout=10,
            sslmode='require'
        )
        cur = conn.cursor()
        
        # Check if table exists
        cur.execute("SELECT to_regclass('public.system_config');")
        exists = cur.fetchone()[0]
        
        if not exists:
            print("Creating system_config table...")
            cur.execute("""
                CREATE TABLE system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert defaults
            print("Inserting default values...")
            cur.execute("""
                INSERT INTO system_config (key, value) VALUES 
                ('form_link', 'https://forms.office.com/r/example'),
                ('start_date', '2024-02-16'),
                ('end_date', '2024-02-18'),
                ('default_reason', 'Home Visit');
            """)
            conn.commit()
            print("system_config table created and populated successfully.")
        else:
            print("system_config table already exists. Checking contents...")
            cur.execute("SELECT * FROM system_config;")
            rows = cur.fetchall()
            if not rows:
                 print("Table exists but is empty. Inserting defaults...")
                 cur.execute("""
                    INSERT INTO system_config (key, value) VALUES 
                    ('form_link', 'https://forms.office.com/r/example'),
                    ('start_date', '2024-02-16'),
                    ('end_date', '2024-02-18'),
                    ('default_reason', 'Home Visit');
                """)
                 conn.commit()
                 print("Defaults inserted.")
            else:
                for row in rows:
                    print(f"  {row}")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_config_table()
