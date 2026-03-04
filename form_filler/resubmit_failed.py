"""
Resubmit all recently failed submissions by calling the same queue logic used by auto_submit_from_email.
This script directly adds tasks to the automation queue for each failed user.
Run from the form_filler directory.
"""
import os, sys, time, threading, json
sys.path.append(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

import psycopg2.extras
from db import get_db_connection
from auth_system_v2 import decrypt_outlook_password

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Find all failed submissions in the last 48 hours (skipping test/dummy URLs)
cur.execute("""
    SELECT sh.id, sh.user_id, sh.form_url, sh.task_id, sh.leave_start_date, sh.leave_end_date, sh.status, sh.message,
           u.email, u.outlook_password_encrypted,
           sp.full_name, sp.roll_number, sp.school, sp.programme, sp.specialization,
           sp.academic_year, sp.student_phone, sp.student_email,
           sp.parent1_name, sp.parent1_phone, sp.parent1_email,
           sp.parent2_name, sp.parent2_phone, sp.parent2_email,
           sp.default_reason
    FROM submission_history sh
    JOIN users u ON u.id = sh.user_id
    LEFT JOIN student_profiles sp ON sp.user_id = sh.user_id
    WHERE sh.status = 'failed'
      AND sh.submitted_at > NOW() - INTERVAL '48 hours'
      AND sh.form_url NOT LIKE '%dummy%'
      AND sh.form_url NOT LIKE '%example%'
    ORDER BY sh.id DESC
""")

failed = cur.fetchall()
print(f"\n{'='*60}")
print(f"Found {len(failed)} failed submissions to retry")
print(f"{'='*60}")

if len(failed) == 0:
    print("Nothing to resubmit.")
    conn.close()
    sys.exit(0)

for f in failed:
    print(f"  [{f['id']}] {f['email']} | {f['leave_start_date']} -> {f['leave_end_date']} | {(f['message'] or '')[:80]}")

print(f"\n{'='*60}")
confirm = input("Proceed with resubmission? (yes/no): ").strip().lower()
if confirm != 'yes':
    print("Aborted.")
    conn.close()
    sys.exit(0)

# Import the normalize function  
from api import normalize_programme, generate_outing_pdf_buffer, get_ist_now

requeued = 0
for f in failed:
    try:
        user_id = f['user_id']
        email = f['email']
        form_url = f['form_url']
        start_date = str(f['leave_start_date'])
        end_date = str(f['leave_end_date'])
        
        # Check if there's already a completed or queued submission for same user+date
        cur.execute("""
            SELECT 1 FROM submission_history 
            WHERE user_id = %s AND leave_start_date = %s AND status IN ('queued', 'running', 'completed')
        """, (user_id, start_date))
        if cur.fetchone():
            print(f"  SKIP {email}: already has queued/completed submission for {start_date}")
            continue
        
        # Decrypt password
        try:
            outlook_password = decrypt_outlook_password(f['outlook_password_encrypted'])
        except Exception as e:
            print(f"  SKIP {email}: password decryption failed: {e}")
            continue
        
        reason = f.get('default_reason') or 'Home Visit'
        
        # Generate PDF
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        profile_data = dict(f)
        profile_data['academic_year'] = f.get('academic_year', '')
        
        pdf_buffer = generate_outing_pdf_buffer(profile_data, start_date, end_date, reason)
        if not pdf_buffer:
            print(f"  SKIP {email}: PDF generation failed")
            continue
        
        task_id = f"retry_{user_id}_{get_ist_now().strftime('%Y%m%d%H%M%S')}"
        pdf_path = os.path.join(temp_dir, f"{task_id}.pdf")
        with open(pdf_path, 'wb') as pf:
            pf.write(pdf_buffer.getvalue() if hasattr(pdf_buffer, 'getvalue') else pdf_buffer)
        
        # Upload PDF to Azure
        try:
            from azure_storage_helper import upload_to_azure_blob
            with open(pdf_path, 'rb') as pf:
                upload_result = upload_to_azure_blob(pf.read(), f"{task_id}.pdf")
            blob_name = upload_result['blob_name']
            pdf_url = upload_result['public_url']
        except Exception as e:
            print(f"  WARN {email}: Azure upload failed ({e}), using local path")
            blob_name = None
            pdf_url = pdf_path
        
        # Prepare form data
        form_data = {
            'student_name': f['full_name'],
            'roll_number': f['roll_number'],
            'school': f['school'],
            'academic_session': f.get('academic_year', ''),
            'programme': normalize_programme(f['programme']),
            'specialization': f.get('specialization', ''),
            'student_phone': f.get('student_phone', ''),
            'student_email': (
                email if (email and 'woxsen.edu.in' in email.lower())
                else (f.get('student_email') or email)
            ),
            'parent_name': f.get('parent1_name', ''),
            'parent_phone': f.get('parent1_phone', ''),
            'parent_email': f.get('parent1_email', ''),
            'parent2_name': f.get('parent2_name'),
            'parent2_phone': f.get('parent2_phone'),
            'reason': reason,
            'leave_start_date': start_date,
            'leave_end_date': end_date,
            'send_parent_email': False
        }
        
        # Insert into submission_history
        cur.execute("""
            INSERT INTO submission_history 
            (user_id, task_id, form_url, leave_start_date, leave_end_date, status, pdf_path, ip_address, blob_name, form_data)
            VALUES (%s, %s, %s, %s, %s, 'queued', %s, '127.0.0.1', %s, %s)
        """, (user_id, task_id, form_url, start_date, end_date, pdf_url, blob_name, json.dumps(form_data)))
        conn.commit()
        
        # Add to automation queue (imported from api.py)
        from api import automation_queue, AutomationTask, automation_tasks
        task = AutomationTask(task_id, user_id)
        automation_tasks[task_id] = task
        
        automation_queue.put({
            'task_id': task_id,
            'user_id': user_id,
            'form_url': form_url,
            'email': email,
            'password': outlook_password,
            'form_data': form_data,
            'pdf_path': pdf_path,
            'blob_name': blob_name
        })
        
        requeued += 1
        print(f"  ✅ Queued: {email} ({task_id})")
        
        # Small delay to avoid hammering
        time.sleep(1)
        
    except Exception as e:
        print(f"  ❌ Error for {f.get('email', 'unknown')}: {e}")

print(f"\n{'='*60}")
print(f"Resubmission complete: {requeued}/{len(failed)} tasks queued")
print(f"{'='*60}")

conn.close()
