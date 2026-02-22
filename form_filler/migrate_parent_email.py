import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'form_filler'))
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
try:
    # Add column if not exists
    cur.execute("""
        ALTER TABLE student_profiles 
        ADD COLUMN IF NOT EXISTS send_parent_email BOOLEAN DEFAULT false
    """)
    conn.commit()
    print("Added send_parent_email to student_profiles.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
