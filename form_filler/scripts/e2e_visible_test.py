"""
End-to-end visible test for one failed paid user.
Runs in NON-HEADLESS mode so the user can watch the browser.
"""
import sys, json, time
sys.path.insert(0, '.')
from db import get_db_connection
from auth_system_v2 import decrypt_outlook_password
import psycopg2.extras
from ms_form_automation import MSFormAutomation

def run_e2e_test():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Pick any failed retry task (not Avinash who has login issues)
    cur.execute("""
        SELECT sh.task_id, sh.form_url, sh.form_data, u.email, u.outlook_password_encrypted, sh.pdf_path
        FROM submission_history sh
        JOIN users u ON sh.user_id = u.id
        WHERE sh.status = 'failed'
          AND u.email != 'avinash.kumar_2028@woxsen.edu.in'
          AND sh.submitted_at > CURRENT_DATE
        ORDER BY sh.submitted_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print("No failed task found to test.")
        return

    print(f"=== END-TO-END VISIBLE TEST ===")
    print(f"Task: {row['task_id']}")
    print(f"User: {row['email']}")
    print(f"Form: {row['form_url']}")
    
    password = decrypt_outlook_password(row['outlook_password_encrypted'])
    
    form_data = row['form_data']
    if isinstance(form_data, str):
        form_data = json.loads(form_data)
    
    print(f"Form Data Keys: {list(form_data.keys())}")
    print(f"Start Date: {form_data.get('leave_start_date')}")
    print(f"End Date: {form_data.get('leave_end_date')}")
    print(f"PDF Path: {row.get('pdf_path')}")
    
    # Run with headless=False so user can watch
    automation = MSFormAutomation(headless=False, min_delay=1, max_delay=3)
    
    try:
        result = automation.run_automation(
            form_url=row['form_url'],
            email=row['email'],
            password=password,
            form_data=form_data,
            pdf_path=row.get('pdf_path'),
            status_callback=lambda msg, prog, img: print(f"[{prog}%] {msg}")
        )
        print(f"\n=== RESULT: {'SUCCESS' if result else 'FAILED'} ===")
        
    except Exception as e:
        print(f"\n=== ERROR: {e} ===")
        import traceback
        traceback.print_exc()
    
    print("Keeping browser open for 60 seconds for inspection...")
    time.sleep(60)
    automation.stop()

if __name__ == "__main__":
    run_e2e_test()
