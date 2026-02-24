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

cur.execute(
    "SELECT p.user_id, u.email, p.plan_type, s.plan_type AS sub_plan "
    "FROM payments p JOIN subscriptions s ON p.user_id = s.user_id "
    "JOIN users u ON p.user_id = u.id "
    "WHERE p.status = 'completed' AND s.plan_type = 'free'"
)
still_free = cur.fetchall()
print(f"REMAINING UNFIXED: {len(still_free)}")
if still_free:
    for r in still_free:
        print(f"  {r['email']}")
else:
    print("  NONE - All paid users are upgraded!")

cur.close()
conn.close()
