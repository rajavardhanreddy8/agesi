import sys
sys.path.insert(0, '.')
import psycopg2.extras
from db import get_db_connection
from cryptography.fernet import Fernet
import os

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get Ansh's profile
cur.execute("""
    SELECT u.id, u.email, u.outlook_password_encrypted,
           p.full_name, p.roll_number, p.school, p.programme,
           p.phone, p.father_name, p.father_email, p.father_phone,
           p.mother_name, p.mother_email, p.mother_phone
    FROM users u
    LEFT JOIN profiles p ON p.user_id = u.id
    WHERE u.email LIKE '%ansh.dhingra%'
""")
user = cur.fetchone()

if not user:
    print("User not found!")
else:
    print(f"Email:    {user['email']}")
    print(f"Name:     {user['full_name']}")
    print(f"Roll No:  {user['roll_number']}")
    print(f"School:   {user['school']}")
    print(f"Outlook pass encrypted: {'SET' if user['outlook_password_encrypted'] else 'MISSING ⚠️'}")

# Also check the active outing config
cur.execute("SELECT form_link, default_reason, start_date, end_date FROM outing_config ORDER BY updated_at DESC LIMIT 1")
config = cur.fetchone()
print(f"\nActive outing config:")
print(f"  form_link:  {config['form_link'] if config else 'NOT SET ⚠️'}")
print(f"  reason:     {config['default_reason'] if config else 'N/A'}")
print(f"  dates:      {config['start_date']} → {config['end_date']}" if config else "  dates: N/A")

conn.close()
