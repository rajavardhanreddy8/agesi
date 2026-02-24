"""Normalize all plan_type values to 'basic' in subscriptions and payments tables."""
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

# Normalize subscriptions: plan -> basic, premium -> basic
cur.execute("UPDATE subscriptions SET plan_type = 'basic' WHERE plan_type IN ('plan', 'premium')")
print(f"Subscriptions normalized: {cur.rowcount} rows updated")

# Normalize payments: plan -> basic, premium -> basic
cur.execute("UPDATE payments SET plan_type = 'basic' WHERE plan_type IN ('plan', 'premium')")
print(f"Payments normalized: {cur.rowcount} rows updated")

conn.commit()

# Verify
cur.execute("SELECT plan_type, COUNT(*) as cnt FROM subscriptions GROUP BY plan_type")
print("\nAfter fix - Subscriptions:")
for r in cur.fetchall():
    print(f"  {r['plan_type']}: {r['cnt']}")

cur.execute("SELECT plan_type, COUNT(*) as cnt FROM payments GROUP BY plan_type")
print("\nAfter fix - Payments:")
for r in cur.fetchall():
    print(f"  {r['plan_type']}: {r['cnt']}")

cur.close()
conn.close()
print("\nDone!")
