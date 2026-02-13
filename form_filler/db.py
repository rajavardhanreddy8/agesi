import os
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path, override=False)

def get_db_connection():
    db_host = os.getenv('DB_HOST')
    try:
        # Standard connection using hostname (Pooler is IPv4)
        conn = psycopg2.connect(
            host=db_host,
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER', 'postgres.uehkqlamchtdzcusqmhi'), # HARDCODED FIX as seen in api.py
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            connect_timeout=10,
            sslmode='require'
        )
        print("DEBUG: DB Connection SUCCESS!", flush=True)
        return conn
    except Exception as e:
        print(f"DEBUG: DB Connection FAILED: {e}", flush=True)
        raise e
