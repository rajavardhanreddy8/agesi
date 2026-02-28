import os
from dotenv import load_dotenv
import psycopg2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT', '5432')

print(f"Connecting to {db_host}...")
try:
    conn = psycopg2.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        dbname=db_name,
        port=db_port,
        connect_timeout=10,
        sslmode='require'
    )
    cur = conn.cursor()
    cur.execute("ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS send_parent_email BOOLEAN DEFAULT TRUE;")
    conn.commit()
    print("Column 'send_parent_email' added successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
