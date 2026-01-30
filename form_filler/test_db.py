import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')
print(f"Testing Connection to: {DB_URL.split('@')[1] if DB_URL and '@' in DB_URL else 'Invalid URL'}")

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print("✅ SUCCESS! Connected to:")
    print(db_version[0])
    cur.close()
    conn.close()
except Exception as e:
    print("❌ FAILURE! Could not connect.")
    print(e)
