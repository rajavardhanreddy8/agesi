import psycopg2
import os
import requests
import json
from api import get_db_connection

def trigger_test():
    try:
        # 1. Update DB to make User 7 eligible
        print("UPDATE subscriptions SET is_auto_submit = TRUE, subscription_end = '2026-12-31' WHERE user_id = 7")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE subscriptions SET is_auto_submit = TRUE, subscription_end = '2026-12-31' WHERE user_id = 7")
        
        # Clear existing tasks for today to avoid skipping
        print("Cleaning up old tasks for User 7...")
        cur.execute("DELETE FROM submission_history WHERE user_id = 7")
        
        conn.commit()
        
        # DEBUG: Check eligibility query
        print("🔍 Checking eligibility query result:")
        cur.execute("""
            SELECT u.id, u.email, s.is_auto_submit, s.subscription_end, u.is_active
            FROM users u
            JOIN subscriptions s ON u.id = s.user_id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE s.is_auto_submit IS TRUE 
              AND s.subscription_end >= CURRENT_DATE
              AND u.is_active IS TRUE
        """)
        print(cur.fetchall())
        
        conn.close()
        print("✅ User 12 updated.")

        # 2. Trigger Automation
        url = 'http://localhost:5000/api/auto-submit-from-email'
        payload = {
            'form_url': 'https://forms.office.com/r/sXXXCpkSWY',
            'start_date': '2026-02-13',
            'end_date': '2026-02-14',
            'reason': 'Final Verification Check'
        }
        print(f"Triggering {url} with {payload}...")
        response = requests.post(url, json=payload)
        
        print("\nAPI Response:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    trigger_test()
