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
from mail_agent.gmail_service import send_email

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
                import time
                # Ensure directory exists
                os.makedirs('screenshots', exist_ok=True)
                
                filename = f"screenshots/{task_id}_{int(time.time())}.jpg"
                with open(filename, "wb") as f:
                    f.write(screenshot_bytes)
                
                # Update DB with screenshot path
                update_db_status(task_id, None, msg, screenshot_path=filename)
            else:
                update_db_status(task_id, None, msg)
        
        def verification_wrapper(scraped_data, screenshot_bytes):
             if not verify_form_data_with_groq:
                 print("Grok verification disabled/unavailable")
                 return True, "Grok Service not available"
             return verify_form_data_with_groq(scraped_data, form_data)

        # Handle PDF URL (download if needed)
        local_pdf_path = pdf_path
        temp_pdf_created = False
        
        if pdf_path.startswith(('http://', 'https://')):
            print(f"DEBUG: Downloading PDF from {pdf_path}")
            import requests
            import tempfile
            
            try:
                response = requests.get(pdf_path, timeout=30)
                if response.status_code == 200:
                    # Create temp file
                    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
                    os.close(fd)
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    local_pdf_path = temp_path
                    temp_pdf_created = True
                    print(f"DEBUG: Saved to temp file {local_pdf_path}")
                else:
                    update_db_status(task_id, 'failed', f"Failed to download PDF: {response.status_code}")
                    return
            except Exception as e:
                 update_db_status(task_id, 'failed', f"PDF Download Error: {str(e)}")
                 return

        success = automation.run_automation(
            form_url, email, password, form_data, local_pdf_path,
            status_callback=status_callback,
            verification_callback=verification_wrapper
        )
        
        # Cleanup temp file
        if temp_pdf_created and os.path.exists(local_pdf_path):
            try:
                os.remove(local_pdf_path)
                print(f"DEBUG: Removed temp PDF {local_pdf_path}")
            except:
                pass
        
        if success:
            update_db_status(task_id, 'completed', 'Automation Success')
            
            # Send Confirmation Emails
            try:
                student_addr = form_data.get('student_email')
                parent_addr = form_data.get('parent_email')
                student_name = form_data.get('student_name', 'Student')
                start_date = form_data.get('leave_start_date')
                end_date = form_data.get('leave_end_date')
                
                subject = f"OUTING SUCCESS: {student_name} ({start_date} to {end_date})"
                body = (
                    f"Hello {student_name},\n\n"
                    f"Your outing form for {start_date} to {end_date} has been successfully submitted automatically.\n\n"
                    f"Status: COMPLETED\n"
                    f"PDF Proof: {pdf_path}\n\n"
                    f"Regards,\nCampus Outing Team"
                )
                html_body = f"""
                <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #10b981;">✅ Outing Form Submitted!</h2>
                    <p>Hello <b>{student_name}</b>,</p>
                    <p>Good news! Your outing permission for <b>{start_date}</b> to <b>{end_date}</b> has been submitted successfully to the Microsoft Form.</p>
                    <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <b>Submission Details:</b><br/>
                        Status: <span style="color: #10b981; font-weight: bold;">SUCCESS</span><br/>
                        Start Date: {start_date}<br/>
                        End Date: {end_date}<br/>
                    </div>
                    <p>You can view your generated PDF here: <a href="{pdf_path}" style="color: #6366f1; text-decoration: none; font-weight: bold;">View PDF Proof</a></p>
                    <p style="color: #6b7280; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px;">
                        This is an automated notification. Please ensure you carry your ID card when leaving the campus.
                    </p>
                </div>
                """
                
                # Send to student
                if student_addr:
                    send_email(student_addr, subject, body, html_body)
                
                # Send to parent (using a slightly different message)
                if parent_addr:
                    parent_body = body.replace(f"Hello {student_name}", "Hello Parent")
                    parent_html = html_body.replace(f"Hello <b>{student_name}</b>", "Hello Parent")
                    send_email(parent_addr, subject, parent_body, parent_html)
                    
            except Exception as mail_err:
                print(f"Failed to send confirmation emails: {mail_err}")
                
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
