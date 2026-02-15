"""Find all tables in the database"""
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# List all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")

tables = cur.fetchall()
print("=== ALL TABLES ===")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
