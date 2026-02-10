
import os
import psycopg2
from dotenv import load_dotenv

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
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print("Tables:", tables)
    
    # Check if there's a config table
    for table in tables:
        t_name = table[0]
        print(f"\n--- {t_name} ---")
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t_name}'")
        columns = cur.fetchall()
        for col in columns:
            print(f"{col[0]} ({col[1]})")
            
    conn.close()
