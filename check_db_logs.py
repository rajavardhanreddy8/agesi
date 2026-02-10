
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Hardcode the credentials from previous context or rely on .env
# The user's env file is open: c:\Users\admin\Documents\outing\agent 4.0\.env

try:
    load_dotenv(override=True)
    
    # Credentials from previous successful connection
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER', 'postgres.uehkqlamchtdzcusqmhi')
    db_pass = os.environ.get('DB_PASSWORD')
    db_port = os.environ.get('DB_PORT', 5432)

    print(f"Connecting to {db_host}...")
    
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pass,
        port=db_port,
        sslmode='require'
    )
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("\n--- Latest 5 Payments ---")
    cur.execute("SELECT id, user_id, plan_type, amount, status, created_at, payment_gateway, payment_order_id, payment_id FROM payments ORDER BY created_at DESC LIMIT 5")
    payments = cur.fetchall()
    for row in payments:
        print(f"Payment {row['id']}: {row['status']} | Order: {row['payment_order_id']} | PayID: {row['payment_id']} | Date: {row['created_at']}")

    print("\n--- Latest 5 Activity Logs ---")
    cur.execute("SELECT id, user_id, action, description, created_at FROM activity_logs ORDER BY created_at DESC LIMIT 5")
    logs = cur.fetchall()
    for row in logs:
        print(f"Log {row['id']}: {row['action']} - {row['description']} | Date: {row['created_at']}")
        
    conn.close()

except Exception as e:
    print(f"Error accessing DB: {e}")
