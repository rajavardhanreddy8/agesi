from dotenv import load_dotenv
from pathlib import Path
import os, psycopg2, psycopg2.extras

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=os.getenv('DB_PORT', 5432)
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT plan_type, COUNT(*) as cnt FROM subscriptions GROUP BY plan_type")
for r in cur.fetchall():
    print(f"SUB: {r['plan_type']} = {r['cnt']}")

cur.execute("SELECT plan_type, COUNT(*) as cnt FROM payments GROUP BY plan_type")
for r in cur.fetchall():
    print(f"PAY: {r['plan_type']} = {r['cnt']}")

cur.close()
conn.close()
