
import psycopg2
import os
import sys

# Credentials from App Service (Session Pooler)
DB_HOST = "aws-1-ap-northeast-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.uehkqlamchtdzcusqmhi"
DB_PASS = "trZaKdFk6MMCb8NY" # From User
DB_PORT = "5432"

print(f"Testing connection to {DB_HOST}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        connect_timeout=10,
        sslmode='prefer'
    )
    print("✅ Connection SUCCESS!")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"Server Version: {version[0]}")
    
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"❌ Connection FAILED: {e}")
    sys.exit(1)
