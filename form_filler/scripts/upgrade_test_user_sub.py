import sys
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Get users
cur.execute("SELECT id, email FROM users WHERE email='test_new@woxsen.edu.in'")
users = cur.fetchall()
print("test_new user:", users)

if users:
    user_id = users[0][0]
    
    # Check if they have a subscription
    cur.execute("SELECT * FROM subscriptions WHERE user_id=%s", (user_id,))
    subs = cur.fetchall()
    print("existing subscriptions:", subs)
    
    if subs:
        cur.execute("UPDATE subscriptions SET plan_type='premium' WHERE user_id=%s RETURNING plan_type", (user_id,))
        print("Updated plan:", cur.fetchall())
    else:
        # Create a subscription
        cur.execute("INSERT INTO subscriptions (user_id, plan_type, subscription_status, is_auto_submit) VALUES (%s, 'premium', 'active', TRUE) RETURNING plan_type", (user_id,))
        print("Created plan:", cur.fetchall())

conn.commit()
cur.close()
conn.close()
