
import os
import psycopg2
from dotenv import load_dotenv

# Load env
load_dotenv()

# DB Config
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT')

def get_db_connection():
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )
    return conn

def check_user():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        target_email = 'guntaka.reddy_2028@woxsen.edu.in'
        print(f"Checking user: {target_email}...")
        
        cur.execute("""
            SELECT u.id, u.email, sp.student_email, sp.full_name, sp.programme 
            FROM users u
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE u.email = %s
        """, (target_email,))
        user_row = cur.fetchone()
        
        if user_row:
            print(f"[FOUND] User Found:")
            print(f"   ID: {user_row[0]}")
            print(f"   EMAIL (Login): {ascii(user_row[1])}")
            print(f"   STUDENT_EMAIL (Profile): {ascii(user_row[2])}")
            print(f"   FULL_NAME: {ascii(user_row[3])}")
            print(f"   PROGRAMME: {ascii(user_row[4])}")
            
            # Simulate Logic
            email_login = user_row[1]
            email_profile = user_row[2]
            
            final_email = (
                email_login if (email_login and 'woxsen.edu.in' in email_login.lower())
                else (email_profile or email_login)
            )
            print(f"\n[INFO] LOGIC SIMULATION:")
            print(f"   Using Logic: (Login Email if Woxsen) ELSE (Profile Email OR Login Email)")
            print(f"   [RESULT] RESULT: {final_email}")
            
            if 'woxsen.edu.in' in final_email:
                print("   [SUCCESS] Logic selects a WOXSEN email.")
            else:
                print("   [FAILURE] Logic selects a NON-WOXSEN email.")
                
        else:
            print("[ERROR] User not found in DB.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_user()
