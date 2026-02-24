"""
Script to fix users who paid but whose subscription was not upgraded.
1. Finds completed payments where the subscription is still 'free'
2. Updates their subscription to the correct plan
3. Logs the fix in activity_logs
"""
from dotenv import load_dotenv
from pathlib import Path
import os, psycopg2, psycopg2.extras
from datetime import datetime, timedelta

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')

SUBSCRIPTION_PLANS = {
    'plan': {
        'name': 'Plan',
        'price': 50,
        'currency': 'INR',
        'duration_days': 30,
        'features': {
            'monthly_submissions': 9999,
            'auto_submit': True,
        }
    }
}

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=os.getenv('DB_PORT', 5432)
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Step 1: Find affected users - completed payment but still on free plan
print("=" * 60)
print("STEP 1: Finding users with completed payments but free plan")
print("=" * 60)

cur.execute("""
    SELECT p.user_id, p.plan_type AS paid_plan, p.status, p.completed_at, p.created_at AS payment_created,
           s.plan_type AS current_plan, s.subscription_start, s.subscription_end,
           u.email
    FROM payments p
    JOIN subscriptions s ON p.user_id = s.user_id
    JOIN users u ON p.user_id = u.id
    WHERE p.status = 'completed'
      AND s.plan_type = 'free'
    ORDER BY p.created_at DESC
""")
affected = cur.fetchall()
print(f"Found {len(affected)} affected users:\n")
for r in affected:
    print(f"  Email: {r['email']}")
    print(f"  User ID: {r['user_id']}")
    print(f"  Paid plan: {r['paid_plan']}")
    print(f"  Payment status: {r['status']}")
    print(f"  Current plan: {r['current_plan']}")
    print(f"  Payment date: {r['payment_created']}")
    print()

# Also check for pending payments (might indicate failed verification)
print("=" * 60)
print("STEP 1b: Checking for pending payments")
print("=" * 60)
cur.execute("""
    SELECT p.user_id, p.plan_type, p.status, p.created_at, u.email
    FROM payments p
    JOIN users u ON p.user_id = u.id
    WHERE p.status != 'completed'
    ORDER BY p.created_at DESC
""")
pending = cur.fetchall()
print(f"Found {len(pending)} non-completed payments:\n")
for r in pending:
    print(f"  Email: {r['email']}, Plan: {r['plan_type']}, Status: {r['status']}, Created: {r['created_at']}")

# Step 2: Fix affected users
if affected:
    print("\n" + "=" * 60)
    print("STEP 2: Fixing affected users")
    print("=" * 60)

    for r in affected:
        user_id = r['user_id']
        paid_plan = r['paid_plan']
        plan_config = SUBSCRIPTION_PLANS.get(paid_plan)

        if not plan_config:
            print(f"  SKIP: Unknown plan '{paid_plan}' for user {r['email']}")
            continue

        sub_end = datetime.now() + timedelta(days=plan_config['duration_days'])
        features = plan_config['features']

        cur.execute("""
            UPDATE subscriptions SET
                plan_type = %s,
                is_auto_submit = %s,
                monthly_submissions_limit = %s,
                subscription_start = CURRENT_DATE,
                subscription_end = %s
            WHERE user_id = %s
        """, (paid_plan, features['auto_submit'], features['monthly_submissions'], sub_end, user_id))

        cur.execute("""
            INSERT INTO activity_logs (user_id, action, description)
            VALUES (%s, 'subscription_fix', %s)
        """, (user_id, f"Admin fix: Upgraded to {plan_config['name']} (payment was completed but subscription was not updated)"))

        print(f"  FIXED: {r['email']} -> plan={paid_plan}, ends={sub_end.date()}")

    conn.commit()
    print(f"\n  All {len(affected)} users fixed and committed!")
else:
    print("\n  No affected users found - all payments properly reflected.")

# Step 3: Verify
print("\n" + "=" * 60)
print("STEP 3: Verification - current subscription status")
print("=" * 60)
cur.execute("""
    SELECT u.email, s.plan_type, s.subscription_start, s.subscription_end, s.is_auto_submit
    FROM subscriptions s
    JOIN users u ON s.user_id = u.id
    WHERE s.plan_type != 'free'
    ORDER BY s.subscription_start DESC
""")
upgraded = cur.fetchall()
print(f"Users with active paid plans: {len(upgraded)}")
for r in upgraded:
    print(f"  {r['email']}: plan={r['plan_type']}, start={r['subscription_start']}, end={r['subscription_end']}")

cur.close()
conn.close()
print("\nDone!")
