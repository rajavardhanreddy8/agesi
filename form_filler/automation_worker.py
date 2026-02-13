import sys
import os
from pathlib import Path

# Add project root and mail_agent to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / 'mail_agent'))

from dotenv import load_dotenv
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path, override=False)

import json
import traceback
import base64
from ms_form_automation import MSFormAutomation
from db import get_db_connection
from mail_agent.groq_service import verify_form_data_with_groq

def update_db_status(task_id, status, message=None, screenshot_path=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if status:
            updates.append("status = %s")
            params.append(status)
        
        if message:
            updates.append("message = %s")
            params.append(message)
            
        if screenshot_path:
            updates.append("screenshot_path = %s") 
            params.append(screenshot_path)

        if updates:
            sql = f"UPDATE submission_history SET {', '.join(updates)} WHERE task_id = %s"
            params.append(task_id)
            cur.execute(sql, tuple(params))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Update Failed: {e}")

def run_worker(task_id, form_url, email, password, form_data, pdf_path, blob_name=None):
    print(f"Worker started for {task_id}")
    
    # 1. Update Status to Running
    update_db_status(task_id, 'running', 'Starting browser...')
    
    try:
        automation = MSFormAutomation(headless=True)
        
        def status_callback(msg, prog, screenshot_bytes):
            print(f"Callback: {msg} {prog}%")
            # In a real subprocess, we can't easily update the parent's memory
            # We must rely on DB or file based IPC. 
            # For now, let's just update DB status text.
            update_db_status(task_id, None, msg)
            
            # Simple screenshot handling: Save to file
            if screenshot_bytes:
                timestamp = 0 # Unique ID
                import time
                filename = f"screenshots/{task_id}_{int(time.time())}.jpg"
                with open(filename, "wb") as f:
                    f.write(screenshot_bytes)
                # We could update DB with this filename if we added a column
        
        def verification_wrapper(scraped_data, screenshot_bytes):
             if not verify_form_data_with_groq:
                 print("Grok verification disabled/unavailable")
                 return True, "Grok Service not available"
             return verify_form_data_with_groq(scraped_data, form_data)

        success = automation.run_automation(
            form_url, email, password, form_data, pdf_path,
            status_callback=status_callback,
            verification_callback=verification_wrapper
        )
        
        if success:
             update_db_status(task_id, 'completed', 'Automation Success')
        else:
             update_db_status(task_id, 'failed', 'Automation Failed via implementation')

    except Exception as e:
        print(f"Worker specific error: {e}")
        traceback.print_exc()
        update_db_status(task_id, 'failed', str(e))

if __name__ == "__main__":
    # Expect JSON args from stdin or simple argparse
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_id", required=True)
    parser.add_argument("--form_url", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--form_data_json", required=True)
    parser.add_argument("--pdf_path", required=True)
    parser.add_argument("--blob_name", required=False)
    
    args = parser.parse_args()
    
    # Parse form_data from JSON string
    form_data = json.loads(args.form_data_json)
    
    run_worker(
        args.task_id, args.form_url, args.email, args.password, 
        form_data, args.pdf_path, args.blob_name
    )
