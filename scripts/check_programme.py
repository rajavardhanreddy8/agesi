"""
Quick script to check current user's programme value in the database
"""
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        sslmode='require'
    )

def check_user_programme(user_id=None):
    """Check programme value for a specific user or all users"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if user_id:
        cur.execute("""
            SELECT u.id, u.email, sp.full_name, sp.programme, sp.specialization
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            WHERE u.id = %s
        """, (user_id,))
    else:
        cur.execute("""
            SELECT u.id, u.email, sp.full_name, sp.programme, sp.specialization
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            ORDER BY u.id DESC
            LIMIT 10
        """)
    
    users = cur.fetchall()
    
    print("\n" + "="*80)
    print("USER PROGRAMME VALUES")
    print("="*80)
    
    for user in users:
        print(f"\nUser ID: {user['id']}")
        print(f"Email: {user['email']}")
        print(f"Name: {user['full_name'] or 'N/A'}")
        
        if user['programme']:
            print(f"Programme: '{user['programme']}' ✓")
        else:
            print("Programme: NULL/EMPTY ❌ <-- THIS WILL CAUSE FAILURE!")
            
        print(f"Specialization: {user['specialization'] or 'N/A'}")
    
    conn.close()

if __name__ == '__main__':
    import sys
    
    # Usage: python check_programme.py [user_id]
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    check_user_programme(user_id)
