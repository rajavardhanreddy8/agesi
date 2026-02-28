#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
import csv
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add the parent directory to sys.path so we can import form_filler modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'form_filler'))

from form_filler.ms_form_automation import MSFormAutomation
from form_filler.db import get_db_connection
from form_filler.auth_system_v2 import decrypt_outlook_password
import psycopg2.extras

def status_cb(msg, prog, screen=None):
    # Print status but suppress to avoid extreme console spam during parallel runs
    # print(f"[{prog}%] {msg}")
    pass

def run_single_worker(user_data):
    """
    Executes a single MSFormAutomation run for the given user data.
    """
    worker_id = user_data.get('worker_id', 'Unknown')
    email = user_data.get('email')
    form_url = user_data.get('form_url')
    form_data = user_data.get('form_data')
    
    print(f"[Worker {worker_id}] Starting submission for {email}...")
    
    # 1. Fetch password from DB
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT outlook_password_encrypted FROM users WHERE email = %s', (email,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            raise Exception(f"User {email} not found in database.")
            
        password = decrypt_outlook_password(row['outlook_password_encrypted'])
    except Exception as e:
        return {'worker_id': worker_id, 'email': email, 'status': False, 'error': f"DB/Auth Error: {e}"}

    # 2. Create Dummy PDF
    pdf_path = f"stress_test_upload_{worker_id}.pdf"
    try:
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
    except Exception as e:
        return {'worker_id': worker_id, 'email': email, 'status': False, 'error': f"PDF creation failed: {e}"}

    # 3. Run Automation
    automation = None
    try:
        # We run headless=True for stress testing
        automation = MSFormAutomation(headless=True)
        result = automation.run_automation(
            form_url=form_url,
            email=email,
            password=password,
            form_data=form_data,
            pdf_path=pdf_path,
            status_callback=status_cb
        )
        
        # Save final screenshot
        try:
            automation.page.screenshot(path=f"final_worker_{worker_id}.png")
        except:
            pass
            
        return {'worker_id': worker_id, 'email': email, 'status': result, 'error': None}
        
    except Exception as e:
        # Save error screenshot
        if automation and hasattr(automation, 'page') and automation.page:
            try:
                automation.page.screenshot(path=f"error_worker_{worker_id}.png")
            except:
                pass
        return {'worker_id': worker_id, 'email': email, 'status': False, 'error': str(e)}
        
    finally:
        # Cleanup PDF
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except:
            pass
            
def main():
    parser = argparse.ArgumentParser(description="Stress Test MS Forms Automation")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers to run")
    parser.add_argument("--data", type=str, default="test_users.json", help="Path to JSON test data")
    args = parser.parse_args()
    
    print(f"============================================================")
    print(f"              MS FORMS STRESS TEST RUNNER                   ")
    print(f"============================================================")
    print(f"Workers requested:   {args.workers}")
    print(f"Data file:           {args.data}")
    
    # 1. Load Data
    try:
        with open(args.data, 'r') as f:
            users = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {args.data}: {e}")
        sys.exit(1)
        
    if not users:
        print("❌ No test users found in data file.")
        sys.exit(1)
        
    # 2. Prepare exact list of jobs based on requested workers
    # If workers > len(users), we loop through users to fulfill the requested count
    jobs = []
    for i in range(args.workers):
        user_copy = dict(users[i % len(users)])
        user_copy['worker_id'] = i + 1  # Override worker ID 1..N
        jobs.append(user_copy)
        
    print(f"Total jobs prepared: {len(jobs)}")
    print(f"Starting execution...")
    print(f"============================================================")
    
    start_time = time.time()
    results = []
    
    # 3. Execute in Parallel
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Submit all jobs
        future_to_job = {executor.submit(run_single_worker, job): job for job in jobs}
        
        # Process as they complete
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            try:
                res = future.result()
                results.append(res)
                icon = "✅" if res['status'] else "❌"
                print(f"{icon} [Worker {res['worker_id']}] Finished. Status: {res['status']}")
                if res['error']:
                    print(f"    Error: {res['error']}")
            except Exception as exc:
                print(f"❌ [Worker {job['worker_id']}] Generated an exception: {exc}")
                results.append({'worker_id': job['worker_id'], 'email': job.get('email'), 'status': False, 'error': str(exc)})

    end_time = time.time()
    
    # 4. Write Results CSV
    csv_file = "stress_test_results.csv"
    success_count = 0
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['worker_id', 'email', 'status', 'error'])
        writer.writeheader()
        for r in sorted(results, key=lambda x: x['worker_id']):
            writer.writerow(r)
            if r['status'] is True:
                success_count += 1
                
    print(f"============================================================")
    print(f"                      TEST SUMMARY                          ")
    print(f"============================================================")
    print(f"Total Time:     {end_time - start_time:.2f} seconds")
    print(f"Total Jobs:     {len(jobs)}")
    print(f"Successful:     {success_count}")
    print(f"Failed:         {len(jobs) - success_count}")
    print(f"Results saved:  {os.path.abspath(csv_file)}")
    print(f"============================================================")
    
    if success_count < len(jobs):
        sys.exit(1) # Return non-zero exit code on failure for CI integration
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
