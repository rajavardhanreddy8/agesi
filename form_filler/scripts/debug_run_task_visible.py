import sys, json, os, time
from pathlib import Path
sys.path.insert(0, '.')
from db import get_db_connection
from auth_system_v2 import decrypt_outlook_password
import psycopg2.extras
from ms_form_automation import MSFormAutomation

def run_debug():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Pick a failed task for Avinash for debugging
    cur.execute("""
        SELECT sh.task_id, sh.form_url, sh.form_data, u.email, u.outlook_password_encrypted, sh.pdf_path, sh.blob_name
        FROM submission_history sh
        JOIN users u ON sh.user_id = u.id
        WHERE u.email = 'avinash.kumar_2028@woxsen.edu.in'
        ORDER BY sh.submitted_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print("No task found for Avinash.")
        return

    print(f"DEBUGGING TASK: {row['task_id']}")
    password = decrypt_outlook_password(row['outlook_password_encrypted'])
    
    # We will run with HEADLESS=FALSE so the user can see it.
    automation = MSFormAutomation(headless=False)
    
    form_data = row['form_data']
    if isinstance(form_data, str):
        form_data = json.loads(form_data)
        
    print(f"Starting browser (VISIBLE) for {row['email']}")
    
    try:
        # Use run_automation directly to ensure all logic is identical to worker
        # but we use a non-headless instance. 
        automation.run_automation(
            form_url=row['form_url'],
            email=row['email'],
            password=password,
            form_data=form_data,
            pdf_path=row.get('pdf_path'),
            status_callback=lambda msg, prog, img: print(f"[{prog}%] {msg}")
        )
        
        print("DEBUG COMPLETE. Keeping browser open for 60 seconds...")
        time.sleep(60)
        
    except Exception as e:
        print(f"Error in debug run: {e}")
        import traceback
        traceback.print_exc()
        print("Keeping browser open for 60 seconds for you to inspect...")
        time.sleep(60)
    finally:
        automation.stop()

if __name__ == "__main__":
    run_debug()
