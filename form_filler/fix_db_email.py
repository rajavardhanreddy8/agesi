
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

def fix_email():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        target_email = 'guntaka.reddy_2028@woxsen.edu.in'
        print(f"Fixing email for user: {target_email}...")
        
        # Get User ID
        cur.execute("SELECT id FROM users WHERE email = %s", (target_email,))
        user_row = cur.fetchone()
        
        if user_row:
            user_id = user_row[0]
            print(f"   Found User ID: {user_id}")
            
            # Update student_profiles
            # Copy login email to student_email if it's missing or different
            print(f"   Updating student_profiles.student_email to '{target_email}'...")
            cur.execute("""
                UPDATE student_profiles 
                SET student_email = %s 
                WHERE user_id = %s
            """, (target_email, user_id))
            
            conn.commit()
            print("   ✅ Update SUCCESSfull! Database now has the email.")
            
        else:
            print("❌ User not found in DB.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_email()
