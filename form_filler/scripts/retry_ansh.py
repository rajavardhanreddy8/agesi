"""
retry_ansh.py - Directly runs the MS Form automation for Ansh Dhingra using real DB data.
"""
import sys, os, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

import psycopg2.extras
from db import get_db_connection
from auth_system_v2 import decrypt_outlook_password
from ms_form_automation import MSFormAutomation

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get Ansh's profile and latest failed submission
cur.execute("""
    SELECT sh.id, sh.form_url, sh.leave_start_date, sh.leave_end_date, sh.form_data,
           u.email, u.outlook_password_encrypted,
           sp.full_name, sp.roll_number, sp.school, sp.programme, sp.specialization,
           sp.academic_year, sp.student_phone, sp.student_email,
           sp.parent1_name, sp.parent1_phone, sp.parent1_email,
           sp.parent2_name, sp.parent2_phone, sp.parent2_email,
           sp.default_reason
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    LEFT JOIN student_profiles sp ON sp.user_id = sh.user_id
    WHERE u.email LIKE '%ansh.dhingra%'
      AND sh.status = 'failed'
    ORDER BY sh.submitted_at DESC
    LIMIT 1
""")

row = cur.fetchone()
if not row:
    print("No failed submissions found for ansh.dhingra. Checking all statuses...")
    cur.execute("""
        SELECT sh.id, sh.form_url, sh.leave_start_date, sh.leave_end_date, sh.form_data,
               sh.status, u.email, u.outlook_password_encrypted,
               sp.full_name, sp.roll_number, sp.school, sp.programme, 
               sp.specialization, sp.academic_year, sp.student_phone, sp.student_email,
               sp.parent1_name, sp.parent1_phone, sp.parent1_email,
               sp.parent2_name, sp.parent2_phone, sp.parent2_email,
               sp.default_reason
        FROM submission_history sh
        JOIN users u ON u.id = sh.user_id
        LEFT JOIN student_profiles sp ON sp.user_id = sh.user_id
        WHERE u.email LIKE '%ansh.dhingra%'
        ORDER BY sh.submitted_at DESC LIMIT 1
    """)
    row = cur.fetchone()

if not row:
    print("No submissions at all for Ansh Dhingra. Check the email spelling.")
    conn.close()
    sys.exit(1)

print(f"User: {row['email']}")
print(f"Name: {row['full_name']}")
print(f"Last submission status: {row.get('status', 'failed')}")
print(f"Form URL: {row['form_url']}")
print(f"Dates: {row['leave_start_date']} -> {row['leave_end_date']}")
print(f"Outlook pass: {'SET' if row['outlook_password_encrypted'] else 'MISSING!'}")

if not row['outlook_password_encrypted']:
    print("\n❌ Outlook password is missing for this user — cannot proceed.")
    conn.close()
    sys.exit(1)

try:
    password = decrypt_outlook_password(row['outlook_password_encrypted'])
    print(f"✅ Password decrypted OK (len={len(password)})")
except Exception as e:
    print(f"❌ Failed to decrypt password: {e}")
    conn.close()
    sys.exit(1)

# Build form data
start_date = str(row['leave_start_date'])
end_date = str(row['leave_end_date'])
reason = row.get('default_reason') or 'Home Visit'

form_data = {
    'student_name': row['full_name'],
    'roll_number': row['roll_number'],
    'school': row['school'],
    'academic_session': row.get('academic_year', '2024-2028'),
    'programme': row['programme'],
    'specialization': row.get('specialization', ''),
    'student_phone': row.get('student_phone', ''),
    'student_email': row['email'],
    'parent_name': row.get('parent1_name', ''),
    'parent_phone': row.get('parent1_phone', ''),
    'parent_email': row.get('parent1_email', ''),
    'parent2_name': row.get('parent2_name'),
    'parent2_phone': row.get('parent2_phone'),
    'reason': reason,
    'leave_start_date': start_date,
    'leave_end_date': end_date,
    'send_parent_email': True
}

print(f"\nStarting Playwright automation (headless=False for visibility)...")
print(f"Form: {row['form_url']}")

def progress_cb(msg, pct, extra):
    print(f"  [{pct:3d}%] {msg}")

auto = MSFormAutomation(headless=False)
success = auto.run_automation(
    form_url=row['form_url'],
    email=row['email'],
    password=password,
    form_data=form_data,
    pdf_path=None,       # No PDF path — will generate a dummy
    status_callback=progress_cb
)

print(f"\n{'='*60}")
print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
print(f"{'='*60}")

# Update DB status
cur.execute("""
    UPDATE submission_history SET status = %s 
    WHERE id = %s
""", ('completed' if success else 'failed', row['id']))
conn.commit()
conn.close()
