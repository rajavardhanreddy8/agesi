import sys
sys.path.insert(0, '.')
from db import get_db_connection
import psycopg2.extras

conn = get_db_connection()

# 1. Get all columns from users table
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("Users table columns:", cols)

# 2. Check actual user data for the failing users
cur2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur2.execute("""
    SELECT u.*
    FROM submission_history sh
    JOIN users u ON sh.user_id = u.id
    WHERE sh.status='failed' AND sh.message LIKE '%roll_number%'
    LIMIT 2
""")
users = cur2.fetchall()
for u in users:
    print("\nUser data:", dict(u))

conn.close()
