"""
check_and_notify.py
Checks submission status for all users and sends each one a status email.
"""

import sys
import os
import psycopg2.extras

# Use absolute paths so this works from any cwd
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent 4.0/form_filler
MAIL_AGENT_DIR = os.path.join(BASE_DIR, '..', 'mail_agent')

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.abspath(MAIL_AGENT_DIR))

from db import get_db_connection

try:
    from gmail_service import send_email
    print("✓ Gmail service loaded")
except Exception as e:
    print(f"✗ Could not load Gmail service: {e}")
    send_email = None

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get the most recent submission for every registered user
cur.execute("""
    SELECT 
        u.id AS user_id,
        u.email,
        sh.status,
        sh.submitted_at,
        sh.task_id
    FROM users u
    LEFT JOIN LATERAL (
        SELECT status, submitted_at, task_id
        FROM submission_history
        WHERE user_id = u.id
        ORDER BY submitted_at DESC NULLS LAST
        LIMIT 1
    ) sh ON TRUE
    WHERE u.email IS NOT NULL
      AND u.email NOT LIKE '%admin%'
    ORDER BY u.email
""")

users = cur.fetchall()
print(f"\nFound {len(users)} users to notify\n{'='*60}")

completed = []
failed = []
pending = []
no_submission = []

for user in users:
    status = user.get('status')
    if not status:
        no_submission.append(user)
    elif status == 'completed':
        completed.append(user)
    elif status in ('failed', 'error'):
        failed.append(user)
    else:
        pending.append(user)

print(f"  Completed:       {len(completed)}")
print(f"  Failed/Error:    {len(failed)}")
print(f"  Pending/Other:   {len(pending)}")
print(f"  No submission:   {len(no_submission)}")

if not send_email:
    print("\n[DRY-RUN] Gmail not available — listing what would be sent:\n")
    for user in completed:
        print(f"  WOULD SEND ✅ completed → {user['email']} (at {user['submitted_at']})")
    for user in failed:
        print(f"  WOULD SEND ❌ failed    → {user['email']} (at {user['submitted_at']})")
    for user in pending:
        print(f"  WOULD SEND ⏳ pending   → {user['email']} (at {user['submitted_at']})")
    conn.close()
    sys.exit(0)

def send_status_email(user, status_label, color, message_body):
    name = user['email'].split('@')[0].replace('.', ' ').title()
    email = user['email']
    submitted_at = user.get('submitted_at', 'N/A')
    
    subject = f"CampusOuting — Outing Submission: {status_label}"
    
    plain_body = (
        f"Hi {name},\n\n"
        f"{message_body}\n\n"
        f"Submission time: {submitted_at}\n\n"
        f"— CampusOuting Team\n"
        f"https://campusouting.app"
    )
    
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px;background:#f8fafc;border-radius:12px;">
        <h2 style="color:#1e293b;margin-bottom:4px;">Outing Submission Update</h2>
        <p style="color:#64748b;font-size:0.9rem;margin-top:0;">campusouting.app</p>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;" />
        <p>Hi <strong>{name}</strong>,</p>
        <div style="background:{color}22;border-left:4px solid {color};padding:12px 16px;border-radius:8px;margin:16px 0;">
            <strong style="color:{color};">{status_label}</strong><br/>
            <span style="color:#475569;font-size:0.9rem;">{message_body}</span>
        </div>
        <p style="color:#64748b;font-size:0.85rem;">Processed at: {submitted_at}</p>
        <p style="color:#94a3b8;font-size:0.8rem;margin-top:24px;">
            Questions? Visit <a href="https://campusouting.app" style="color:#6366f1;">campusouting.app</a>
        </p>
    </div>
    """
    
    result = send_email(email, subject, plain_body, html_body=html_body)
    status_icon = "✉️  Sent" if result else "❌  Failed to send"
    print(f"  {status_icon} → {email}")
    return result

print("\n--- Sending emails ---")
sent = errors = 0

for user in completed:
    ok = send_status_email(
        user, "✅ Submission Completed", "#22c55e",
        "Your outing application has been successfully submitted. Your parent will also receive a notification."
    )
    if ok: sent += 1
    else: errors += 1

for user in failed:
    ok = send_status_email(
        user, "⚠️ Submission Failed", "#ef4444",
        "Your outing submission encountered an error. Please log in to campusouting.app and try again, or contact your admin."
    )
    if ok: sent += 1
    else: errors += 1

for user in pending:
    ok = send_status_email(
        user, "⏳ Submission In Progress", "#f59e0b",
        "Your outing submission is being processed. You will receive another email when it's done."
    )
    if ok: sent += 1
    else: errors += 1

print(f"\n{'='*60}")
print(f"  Emails sent:    {sent}")
print(f"  Send errors:    {errors}")
print(f"  Skipped (no submission): {len(no_submission)}")

conn.close()
