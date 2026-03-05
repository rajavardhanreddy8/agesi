
import os
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
from pathlib import Path

# Load from root .env
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

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
        print(f"Connection failed: {e}")
        return None

def check_users():
    conn = get_db_connection()
    if not conn:
        # Fallback to DATABASE_URL if individual vars fail
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                conn = psycopg2.connect(db_url)
            except:
                print("DATABASE_URL fallback failed too.")
                return

    if not conn:
        print("Could not connect to database.")
        return

    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    # Check users and subscriptions
    query = """
    SELECT u.email, s.plan_type, s.monthly_submissions_limit, s.is_auto_submit, s.subscription_end
    FROM users u
    JOIN subscriptions s ON u.id = s.user_id
    ORDER BY s.subscription_end DESC
    LIMIT 30;
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    print(f"{'Email':<50} | {'Plan':<10} | {'Limit':<6} | {'Auto':<5} | {'Ends'}")
    print("-" * 95)
    for row in rows:
        email = row['email']
        plan = row['plan_type'] or "N/A"
        limit = str(row['monthly_submissions_limit']) if row['monthly_submissions_limit'] is not None else "N/A"
        auto = "ON" if row['is_auto_submit'] else "OFF"
        ends = str(row['subscription_end'])
        print(f"{email:<50} | {plan:<10} | {limit:<6} | {auto:<5} | {ends}")
    
    conn.close()

if __name__ == "__main__":
    check_users()
