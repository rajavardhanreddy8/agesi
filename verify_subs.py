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

# Check all paid subscriptions
cur.execute(
    "SELECT u.email, s.plan_type, s.subscription_start, s.subscription_end "
    "FROM subscriptions s JOIN users u ON s.user_id = u.id "
    "WHERE s.plan_type != 'free' ORDER BY s.subscription_start DESC"
)
rows = cur.fetchall()
print(f"Paid users: {len(rows)}")
for r in rows:
    print(f"  {r['email']}: plan={r['plan_type']}, end={r['subscription_end']}")

# Check if any completed payments still have free subscription
cur.execute(
    "SELECT p.user_id, u.email, p.plan_type AS paid_plan, s.plan_type AS current_plan "
    "FROM payments p JOIN subscriptions s ON p.user_id = s.user_id "
    "JOIN users u ON p.user_id = u.id "
    "WHERE p.status = 'completed' AND s.plan_type = 'free'"
)
still_free = cur.fetchall()
print(f"\nStill free after payment: {len(still_free)}")
for r in still_free:
    print(f"  {r['email']}: paid={r['paid_plan']}, current={r['current_plan']}")

cur.close()
conn.close()
