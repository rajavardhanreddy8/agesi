import sys, json
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]

result = {}
for t in tables:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position")
    result[t] = [r[0] for r in cur.fetchall()]

with open('all_tables.json', 'w') as f:
    json.dump(result, f, indent=2)
print("Done, tables:", list(result.keys()))
conn.close()
