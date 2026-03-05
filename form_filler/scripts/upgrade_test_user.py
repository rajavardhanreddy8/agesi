import sys
sys.path.insert(0, '.')
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.execute("""
    UPDATE users 
    SET plan_type = 'premium'
    WHERE email = 'test_new@woxsen.edu.in' OR email = 'test@woxsen.edu.in'
    RETURNING email, plan_type
""")

updated = cur.fetchall()
print("\nUpdated to premium:", updated)

conn.commit()
cur.close()
conn.close()
