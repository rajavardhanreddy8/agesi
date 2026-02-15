
import os
import psycopg2
from api import get_db_connection
from auth_system_v2 import encrypt_outlook_password

def prepare_user_7():
    try:
        # Original plaintext password found in DB
        plaintext_password = "K@nni:18"
        
        # 1. Encrypt the password correctly
        encrypted_password = encrypt_outlook_password(plaintext_password)
        print(f"Encrypted password generated: {encrypted_password[:20]}...")

        # 2. Update DB
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update user table with correct encryption
        print("Updating users table...")
        cur.execute(
            "UPDATE users SET outlook_password_encrypted = %s, is_active = TRUE WHERE id = 7",
            (encrypted_password,)
        )
        
        # Update subscription table
        print("Updating subscriptions table...")
        cur.execute(
            "UPDATE subscriptions SET is_auto_submit = TRUE, subscription_end = '2026-12-31' WHERE user_id = 7"
        )
        
        conn.commit()
        print("✅ User 7 successfully prepared for automation.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error preparing User 7: {e}")

if __name__ == "__main__":
    prepare_user_7()
