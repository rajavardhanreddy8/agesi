import sys, json
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# List all (public) tables
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]
print("ALL Tables:", tables)

# Also list columns per table
for t in tables:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print(f"\n{t}: {cols}")

conn.close()
