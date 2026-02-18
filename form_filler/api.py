"""
Flask API to trigger Microsoft Forms automation
Integrates with your existing PDF generation web app and PostgreSQL database
"""

import httpx
import supabase
# print(f"DEBUG: httpx version: {httpx.__version__}", flush=True)
# print(f"DEBUG: supabase version: {supabase.__version__}", flush=True)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import json
import os
import sys
import logging
import os
import logging
print("DEBUG: API.PY MODULE LOADING...", flush=True)
from datetime import datetime, timedelta
import pytz
from cryptography.fernet import Fernet
from dotenv import load_dotenv
# Force override of environment variables from .env file
import os
from pathlib import Path

# ===== TIMEZONE CONFIGURATION FOR INDIA (IST) =====
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in Indian Standard Time (IST, UTC+5:30)"""
    return datetime.now(IST)

def format_ist_timestamp(dt=None):
    """Format timestamp in IST with readable format"""
    if dt is None:
        dt = get_ist_now()
    return dt.strftime('%Y-%m-%d %H:%M:%S IST')
# ===== END TIMEZONE CONFIGURATION =====

# Force clear existing variables to ensure .env is read
# if 'RAZORPAY_KEY_ID' in os.environ:
#     del os.environ['RAZORPAY_KEY_ID']
# if 'RAZORPAY_KEY_SECRET' in os.environ:
#     del os.environ['RAZORPAY_KEY_SECRET']

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
print(f"DEBUG: Loading .env from: {env_path}", flush=True)
# CRITICAL FIX: Do NOT override system env vars (Azure settings take first priority)
load_dotenv(dotenv_path=env_path, override=False)

load_dotenv(dotenv_path=env_path, override=False)

# Add mail_agent to path for Grok Service
sys.path.append(str(BASE_DIR / 'mail_agent'))
try:
    from groq_service import verify_form_data_with_groq, process_content_with_groq
except ImportError:
    logging.warning("Could not import groq_service. AI Verification will be disabled.")
    verify_form_data_with_groq = None
    process_content_with_groq = None

# Import Gmail Service
try:
    from gmail_service import get_latest_email_content
except ImportError:
    logging.warning("Could not import gmail_service.")
    get_latest_email_content = None

print("="*50, flush=True)
print(f"DEBUG: STARTING APP - {format_ist_timestamp()}", flush=True)
print(f"DEBUG: Loaded DB_HOST: {os.getenv('DB_HOST')}", flush=True)
print(f"DEBUG: Loaded RAZORPAY_KEY_ID: {os.getenv('RAZORPAY_KEY_ID')}", flush=True)
print("="*50, flush=True)

import razorpay
# Initialize Razorpay Client Global
razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')

# Create client only if keys exist to avoid startup crash if env vars missing
if razorpay_key_id and razorpay_key_secret:
    razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
else:
    print("WARNING: Razorpay keys not found in environment", flush=True)
    razorpay_client = None

from functools import wraps
import psycopg2
import psycopg2.extras
import hashlib
from db import get_db_connection

# Import the automation class
try:
    from ms_form_automation import MSFormAutomation
except ImportError:
    MSFormAutomation = None
    logging.warning("Playwright not installed or module not found. Automation features disabled.")

# Import authentication system (Supabase-based)
try:
    from auth_system_v2 import (
        register_user, login_user, verify_email_token,
        request_password_reset, reset_password,
        encrypt_outlook_password, decrypt_outlook_password,
        hash_password, verify_outlook_credentials,
        verify_password, generate_jwt, verify_jwt,
        get_user_profile, supabase, login_required
    )

    def admin_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            try:
                user_res = supabase.table('users').select('is_admin').eq('id', user_id).execute()
                if not user_res.data or not user_res.data[0].get('is_admin'):
                    return jsonify({'success': False, 'error': 'Admin privileges required'}), 403
            except Exception as e:
                return jsonify({'success': False, 'error': f'Auth verification failed: {str(e)}'}), 500
                
            return f(*args, **kwargs)
        return decorated_function

    def subscription_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user_id = getattr(request, 'user_id', None)
            try:
                # Get active subscription
                res = supabase.table('subscriptions').select('*').eq('user_id', user_id).eq('plan_type', 'premium').execute()
                # Simple check: basic or premium? User said "Subscribers only"
                if not res.data:
                    # Check any non-free plan
                    res = supabase.table('subscriptions').select('*').eq('user_id', user_id).neq('plan_type', 'free').execute()
                    if not res.data:
                        return jsonify({'success': False, 'error': 'ACTIVE SUBSCRIPTION REQUIRED! Please upgrade your plan to access this feature.'}), 403
                
                # Check expiry
                sub = res.data[0]
                if sub.get('subscription_end'):
                    end_date = datetime.strptime(sub['subscription_end'], '%Y-%m-%d').date()
                    if end_date < datetime.now().date():
                        return jsonify({'success': False, 'error': 'SUBSCRIPTION EXPIRED! Please renew your plan.'}), 403
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'Subscription check failed: {str(e)}'}), 500
                
            return f(*args, **kwargs)
        return decorated_function
except ImportError as e:
    logging.error(f"Failed to import auth system: {e}")
    raise e

load_dotenv()

app = Flask(__name__)
# Configure CORS with explicit allowed origins
allow_origins = [
    "https://campusouting.app",
    "https://www.campusouting.app",
    "https://agreeable-sky-058124200.4.azurestaticapps.net",
    "http://localhost:5173",
    "http://localhost:3000"
]
CORS(app, resources={r"/*": {"origins": allow_origins}}, supports_credentials=True)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

# Configure logging
# Get the directory where api.py is located
api_dir = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(api_dir, 'automation.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Store active automation tasks
automation_tasks = {}
import queue

# Global Automation Queue for Scalability
automation_queue = queue.Queue()

def automation_worker():
    """Background worker that processes automation tasks from the queue."""
    print("RECOVERY: Background worker thread started.", flush=True)
    logging.info("Automation worker thread started and ready to process tasks")

    # Get the directory where api.py is located (form_filler directory)
    api_dir = os.path.dirname(os.path.abspath(__file__))

    worker_crash_count = 0
    max_consecutive_crashes = 5

    while True:
        try:
            # Use timeout to prevent indefinite blocking
            # If queue is empty, timeout after 30 seconds and reset crash counter
            task_info = automation_queue.get(timeout=30)

            if task_info is None:
                print("Worker received None, stopping.", flush=True)
                logging.info("Worker received stop signal (None)")
                break

            # Reset crash counter on successful task retrieval
            worker_crash_count = 0

            try:
                print(f"DEBUG: Processing task {task_info['task_id']}...", flush=True)
                logging.info(f"Processing queued task: {task_info['task_id']} for user {task_info['user_id']}")

                # Use subprocess to avoid asyncio conflicts with Playwright Sync API
                import subprocess

                # Prepare args - use absolute path for worker script
                worker_script = os.path.join(api_dir, 'automation_worker.py')

                cmd = [
                    sys.executable, "-u", worker_script,
                    "--task_id", task_info['task_id'],
                    "--form_url", task_info['form_url'],
                    "--email", task_info['email'],
                    "--password", task_info['password'],
                    "--form_data_json", json.dumps(task_info['form_data']),
                    "--pdf_path", task_info['pdf_path']
                ]

                if task_info.get('blob_name'):
                    cmd.extend(["--blob_name", task_info['blob_name']])

                # Log file with absolute path
                log_file_path = os.path.join(api_dir, 'automation_worker.log')
                print(f"DEBUG: Log file path: {log_file_path}", flush=True)

                # Force UTF-8 for subprocess output
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

                print(f"DEBUG: Launching subprocess: {' '.join(cmd[:4])}...", flush=True)

                # Open log file and launch subprocess with explicit working directory
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    # Write separator and timestamp
                    log_file.write(f"\n{'='*60}\n")
                    log_file.write(f"Task: {task_info['task_id']} at {format_ist_timestamp()}\n")
                    log_file.write(f"{'='*60}\n")
                    log_file.flush()

                    # Launch subprocess with cwd set to form_filler directory
                    process = subprocess.Popen(
                        cmd,
                        stdout=log_file,
                        stderr=log_file,
                        env=env,
                        cwd=api_dir  # Critical: Set working directory to form_filler
                    )

                # Log the PID for tracking
                logging.info(f"Launched subprocess PID {process.pid} for task {task_info['task_id']}")
                print(f"DEBUG: Subprocess started with PID {process.pid}", flush=True)

            except Exception as e:
                logging.error(f"Worker failed launching subprocess for task {task_info['task_id']}: {e}", exc_info=True)
                # Update DB to failed status if subprocess can't start
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE submission_history SET status = 'failed', error_details = %s WHERE task_id = %s",
                        (f"Subprocess launch failed: {str(e)}", task_info['task_id'])
                    )
                    conn.commit()
                    conn.close()
                except Exception as db_e:
                    logging.error(f"Failed to update DB status: {db_e}", exc_info=True)
            finally:
                automation_queue.task_done()

        except queue.Empty:
            # Queue is empty and timeout expired - this is normal, worker is idle
            print(f"DEBUG: Worker idle (no tasks in queue)", flush=True)
            worker_crash_count = 0
            continue

        except Exception as e:
            # Catch any unexpected errors to prevent worker from crashing
            worker_crash_count += 1
            logging.error(f"CRITICAL: Automation worker encountered unexpected error ({worker_crash_count}/{max_consecutive_crashes}): {e}", exc_info=True)
            print(f"ERROR: Worker error (attempt {worker_crash_count}/{max_consecutive_crashes}): {e}", flush=True)

            if worker_crash_count >= max_consecutive_crashes:
                logging.error(f"CRITICAL: Automation worker crashed {max_consecutive_crashes} times. Stopping worker.")
                print(f"CRITICAL: Worker stopping after {max_consecutive_crashes} consecutive crashes", flush=True)
                break

            # Brief sleep before retrying to avoid rapid crash loops
            import time
            time.sleep(2)

# Start the worker thread
worker_thread = threading.Thread(target=automation_worker, daemon=True)
worker_thread.start()

# Recovery on startup
_recovery_done = False
def init_app_background():
    # Deprecated: now manually triggered via endpoint for debugging stability
    pass

# Call recovery at module level so it runs in Gunicorn
# init_app_background()

class AutomationTask:
    """Track automation task status"""
    def __init__(self, task_id, user_id):
        self.task_id = task_id
        self.user_id = user_id
        self.status = 'pending'
        self.progress = 0
        self.message = 'Queued...'
        self.error = None
        self.start_time = datetime.now()
        self.end_time = None
        self.screenshot_path = None
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'user_id': self.user_id,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'error': self.error,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'screenshot_path': self.screenshot_path
        }

def run_automation_async(task_id, form_url, email, password, form_data, pdf_path, blob_name=None):
    """Run automation logic (called by worker)"""
    task = automation_tasks.get(task_id)
    if not task: return

    conn = None
    try:
        task.status = 'running'
        task.message = 'Starting browser...'
        task.progress = 10
        
        # Update DB status
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE submission_history SET status = 'running' WHERE task_id = %s",
                (task_id,)
            )
            conn.commit()
        except Exception as e:
            logging.error(f"Failed to update DB status: {e}")
        
        # CRITICAL: Create the automation object (headless=True for server)
        automation = MSFormAutomation(headless=True)
        
        def status_callback(msg, prog, screenshot_bytes):
            task.message = msg
            task.progress = prog
            if screenshot_bytes:
                # Save screenshot to task for "Live View"
                # Store it as base64 for simplicity in this demo, or write to tmp file
                import base64
                task.screenshot_path = f"data:image/jpeg;base64,{base64.b64encode(screenshot_bytes).decode('utf-8')}"
            
            # Update DB status message
            try:
                conn_inner = get_db_connection()
                cur_inner = conn_inner.cursor()
                cur_inner.execute(
                    "UPDATE submission_history SET message = %s WHERE task_id = %s",
                    (msg, task_id)
                )
                conn_inner.commit()
                conn_inner.close()
            except:
                pass
        
        # AI Verification Callback
        def verification_wrapper(scraped_data, screenshot_bytes):
            if not verify_form_data_with_groq:
                return True, "Grok Service not available"
            
            # Use form_data as expected source of truth
            return verify_form_data_with_groq(scraped_data, form_data)

        # Run the full workflow
        success = automation.run_automation(
            form_url=form_url,
            email=email,
            password=password,
            form_data=form_data,
            pdf_path=pdf_path,
            status_callback=status_callback,
            verification_callback=verification_wrapper
        )
        
        if success:
            task.status = 'completed'
            task.progress = 100
            task.message = 'Form submitted successfully!'
            task.end_time = datetime.now()
            
            # Update DB
            if conn:
                cur.execute(
                    "UPDATE submission_history SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE task_id = %s",
                    (task_id,)
                )
                
                # Update subscription usage
                cur.execute(
                    "UPDATE subscriptions SET submissions_used = submissions_used + 1 WHERE user_id = %s",
                    (task.user_id,)
                )
                conn.commit()
            
            # Delete PDF from Azure Blob Storage after successful submission
            if blob_name:
                try:
                    from azure_storage_helper import delete_from_azure_blob
                    deletion_success = delete_from_azure_blob(blob_name)
                    if deletion_success:
                        logging.info(f"Successfully deleted PDF from Azure: {blob_name}")
                    else:
                        logging.warning(f"PDF deletion returned false: {blob_name}")
                except Exception as e:
                    # Don't fail the task if deletion fails
                    logging.error(f"Failed to delete PDF from Azure (non-critical): {e}")
        # run_automation now raises an exception with the actual error on failure,
        # so if we reach here, it was successful.
        if not success:
            raise Exception("Automation returned False unexpectedly")
        
    except Exception as e:
        task.status = 'failed'
        task.error = str(e)
        task.message = f'Automation failed: {str(e)}'
        task.end_time = datetime.now()
        logging.error(f"Task {task_id} failed: {str(e)}")
        
        # Update DB
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE submission_history SET status = 'failed', error_details = %s WHERE task_id = %s",
                    (str(e), task_id)
                )
                conn.commit()
            except:
                pass
    finally:
        if conn:
            conn.close()
        # Clean up PDF file
        try:
            if pdf_path and os.path.exists(pdf_path) and "standard_outing" not in pdf_path:
                os.remove(pdf_path)
                logging.info(f"Deleted temporary PDF: {pdf_path}")
        except Exception as e:
            logging.error(f"Failed to delete PDF {pdf_path}: {e}")

@app.route('/api/auto-submit-from-email', methods=['POST'])
def auto_submit_from_email():
    """
    Endpoint triggered by Mail Agent to auto-submit forms for all subscribed users.
    Scalable: Adds tasks to a queue instead of running them immediately.
    """
    try:
        data = request.json
        form_url = data.get('form_url')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        reason = data.get('reason')

        if not form_url or not start_date:
            return jsonify({'success': False, 'error': 'Missing form_url or start_date'}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # DEBUG: List all users to check status
        cur.execute("SELECT id, email, is_active FROM users")
        all_users = cur.fetchall()
        logging.info(f"DEBUG: All users in DB: {all_users}")

        cur.execute("""
            SELECT u.id as user_id, u.email, u.outlook_password_encrypted,
                   sp.full_name, sp.roll_number, sp.school, sp.programme,
                   sp.specialization, sp.academic_year, sp.student_phone, sp.student_email,
                   sp.parent1_name, sp.parent1_email, sp.parent1_phone,
                   sp.parent2_name, sp.parent2_email, sp.parent2_phone,
                   sp.signature_data, sp.default_reason
            FROM users u
            JOIN subscriptions s ON u.id = s.user_id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE s.is_auto_submit IS TRUE 
              AND s.subscription_end >= CURRENT_DATE
              AND u.is_active IS TRUE
        """)
        eligible_users = cur.fetchall()
        logging.info(f"DEBUG: Found {len(eligible_users)} eligible users.")
        
        tasks_created = 0

        for user in eligible_users:
            try:
                user_id = user['user_id']

                # Check for existing pending/completed task for this date
                cur.execute("""
                    SELECT 1 FROM submission_history 
                    WHERE user_id = %s 
                      AND leave_start_date = %s 
                      AND status IN ('queued', 'running', 'completed')
                """, (user_id, start_date))
                
                if cur.fetchone():
                    logging.info(f"Skipping duplicate task for user {user_id} on {start_date}")
                    continue
                
                # Decrypt password
                try:
                    outlook_password = decrypt_outlook_password(user['outlook_password_encrypted'])
                except:
                    logging.error(f"Could not decrypt password for user {user['email']}, skipping.")
                    continue
                # Determine Reason
                out_reason = reason if reason else user.get('default_reason', 'Home Visit')

                # Create Specific PDF with Reason
                temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
                os.makedirs(temp_dir, exist_ok=True)
                pdf_path = os.path.join(temp_dir, f"auto_{user_id}_{get_ist_now().strftime('%Y%m%d%H%M%S')}.pdf")
                logging.info(f"DEBUG: PDF path: {pdf_path}")
                
                # Generate PDF using helper
                pdf_buffer = generate_outing_pdf_buffer(user, start_date, end_date, out_reason)
                logging.info(f"DEBUG: PDF generator returned {type(pdf_buffer)} for user {user_id}")
                if pdf_buffer:
                    with open(pdf_path, 'wb') as f:
                        if hasattr(pdf_buffer, 'getvalue'):
                            f.write(pdf_buffer.getvalue())
                        else:
                            logging.error(f"pdf_buffer is not a buffer! type: {type(pdf_buffer)}")
                            raise Exception(f"Expected buffer, got {type(pdf_buffer)}")
                else:
                    logging.error(f"Failed to generate PDF for user {user_id}, skipping automation.")
                    continue

                # Prepare Form Data
                form_data = {
                    'student_name': user['full_name'],
                    'roll_number': user['roll_number'],
                    'school': user['school'],
                    'academic_session': user['academic_year'],
                    'programme': user['programme'],
                    'specialization': user['specialization'],
                    'student_phone': user['student_phone'],
                    'student_email': user['student_email'] or user['email'],
                    'parent_name': user['parent1_name'],
                    'parent_phone': user['parent1_phone'],
                    'parent_email': user['parent1_email'],
                    'parent2_name': user.get('parent2_name'),
                    'parent2_phone': user.get('parent2_phone'),
                    'reason': out_reason,
                    'leave_start_date': start_date,
                    'leave_end_date': end_date
                }
                # Create Task
                task_id = f"auto_{user_id}_{get_ist_now().strftime('%Y%m%d%H%M%S')}"
                task = AutomationTask(task_id, user_id)
                automation_tasks[task_id] = task

                # Log to DB
                cur.execute(
                    """
                    INSERT INTO submission_history 
                    (user_id, task_id, form_url, leave_start_date, leave_end_date, status, pdf_path, ip_address)
                    VALUES (%s, %s, %s, %s, %s, 'queued', %s, '127.0.0.1')
                    """,
                    (
                        user_id, task_id, form_url,
                        start_date, end_date,
                        pdf_path
                    )
                )
                conn.commit()

                # Add to Queue
                automation_queue.put({
                    'task_id': task_id,
                    'user_id': user_id,
                    'form_url': form_url,
                    'email': user['email'],
                    'password': outlook_password,
                    'form_data': form_data,
                    'pdf_path': pdf_path
                })
                
                tasks_created += 1

            except Exception as u_e:
                logging.error(f"Error preparing task for user {user.get('user_id')}: {u_e}")

        return jsonify({
            'success': True, 
            'message': f'Triggered automation for {tasks_created} users',
            'tasks_queued': tasks_created
        })

    except Exception as e:
        logging.error(f"Auto-submit trigger failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()



# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        result = register_user(data)
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400

        # Unified Login Logic:
        # First check if user exists in our DB
        result = login_user(email, password)

        # If normal login fails, try Outlook verify (for new or password-syncing users)
        if not result['success']:
            print(f"DEBUG: Internal login failed for {email}, trying Outlook direct...", flush=True)
            try:
                outlook_ok, outlook_error = verify_outlook_credentials(email, password)
                if outlook_ok:
                    print(f"DEBUG: Outlook verification successful for {email}", flush=True)
                    # Outlook success! If user exists, update password. If not, register.
                    user_res = supabase.table('users').select('*').eq('email', email).execute()
                    if user_res.data:
                        # Update local password to match Outlook (Unified)
                        supabase.table('users').update({
                            'password_hash': hash_password(password),
                            'outlook_password_encrypted': encrypt_outlook_password(password)
                        }).eq('email', email).execute()
                    else:
                        # Auto-register new Outlook user
                        register_user({
                            'email': email,
                            'password': password,
                            'full_name': email.split('@')[0].replace('.', ' ').title()
                        })
                    # Retry login after sync
                    result = login_user(email, password)
                else:
                    print(f"DEBUG: Outlook verification failed: {outlook_error}", flush=True)
            except Exception as outlook_e:
                print(f"DEBUG: Outlook verification exception: {outlook_e}", flush=True)
                logging.error(f"Outlook verification exception: {outlook_e}", exc_info=True)
                # Don't fail here - just use the internal DB result

        return jsonify(result), 200 if result['success'] else 401
    except Exception as e:
        logging.error(f"Login endpoint exception: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Login system error: {str(e)}'}), 500

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        result = login_user(email, password)
        if result['success']:
            # Verify they actually are an admin
            user_id = result['user']['id']
            user_res = supabase.table('users').select('is_admin').eq('id', user_id).execute()
            if not user_res.data or not user_res.data[0].get('is_admin'):
                return jsonify({'success': False, 'error': 'Insufficient privileges'}), 403
            
            # Persist admin status in user object for frontend
            result['user']['is_admin'] = True
            
        return jsonify(result), 200 if result['success'] else 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/update-form-settings', methods=['POST'])
@admin_required
def api_update_form_settings():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        for key in ['form_link', 'start_date', 'end_date', 'default_reason']:
            if key in data:
                cur.execute("UPDATE system_config SET value = %s, updated_at = NOW() WHERE key = %s", (data[key], key))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Settings updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        # Get basic stats
        res_users = supabase.table('users').select('id', count='exact').execute()
        res_subs = supabase.table('submission_history').select('id', count='exact').execute()
        
        # Calculate revenue (sum payments)
        res_payments = supabase.table('payments').select('amount').eq('status', 'completed').execute()
        total_revenue = sum(p['amount'] for p in res_payments.data) if res_payments.data else 0
        
        # Get recent activity (submission history + some logs)
        res_activity = supabase.table('submission_history').select('*').order('submitted_at', desc=True).limit(10).execute()
        
        # Format activity to match frontend expectations
        formatted_activity = []
        for act in res_activity.data:
            # Need to join with users/profiles for email/name
            user_res = supabase.table('users').select('email').eq('id', act['user_id']).execute()
            email = user_res.data[0]['email'] if user_res.data else "Unknown"
            formatted_activity.append({
                'email': email,
                'action': act['status'].upper(),
                'description': f"Form submission: {act.get('message', 'No details')}",
                'created_at': act['submitted_at']
            })

        return jsonify({
            'success': True,
            'stats': {
                'total_users': res_users.count,
                'total_revenue': float(total_revenue),
                'total_submissions': res_subs.count,
                'queue_size': automation_queue.qsize() if 'automation_queue' in globals() else 0
            },
            'recent_activity': formatted_activity
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    try:
        # Fetch users with profile and subscription info
        # This is a complex join, might need multiple queries if views aren't used
        # Using the view v_user_profiles if it exists
        res = supabase.table('v_user_profiles').select('*').execute()
        return jsonify({'success': True, 'users': res.data})
    except Exception as e:
        # Fallback if view doesn't exist
        try:
            res = supabase.table('users').select('*, student_profiles(*), subscriptions(*)').execute()
            # Flatten or format data
            return jsonify({'success': True, 'users': res.data})
        except:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/submissions', methods=['GET'])
@admin_required
def admin_submissions():
    """Get full submission history for admins"""
    try:
        # Get last 100 submissions
        res = supabase.table('submission_history')\
            .select('*, users(email), student_profiles(full_name, roll_number)')\
            .order('submitted_at', desc=True)\
            .limit(100)\
            .execute()
            
        return jsonify({
            'success': True, 
            'submissions': res.data
        })
    except Exception as e:
        logging.error(f"Failed to fetch submissions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/screenshot/<task_id>', methods=['GET'])
@admin_required
def admin_screenshot(task_id):
    """Serve automation screenshots"""
    try:
        # Get submission details to verify screenshot exists
        res = supabase.table('submission_history').select('screenshot_path').eq('task_id', task_id).execute()
        if not res.data or not res.data[0]['screenshot_path']:
            return "No screenshot available", 404
            
        path = res.data[0]['screenshot_path']
        # Verify path is within form_filler/screenshots, or absolute path
        # The automation worker might save nicely
        if os.path.exists(path):
             return send_file(path)
        
        return "File not found", 404
    except Exception as e:
        return str(e), 500

@app.route('/api/auth/verify-email', methods=['POST'])
def api_verify_email():
    try:
        result = verify_email_token(request.json.get('token'))
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/request-password-reset', methods=['POST'])
def api_request_reset():
    return jsonify(request_password_reset(request.json.get('email')))

@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset():
    data = request.json
    return jsonify(reset_password(data.get('token'), data.get('new_password')))


# ============================================================================
# CONFIGURATION ROUTES
# ============================================================================

@app.route('/api/config/active-outing', methods=['GET'])
def get_active_outing_config():
    """
    Get the latest outing configuration (form link, dates) 
    from the system_config table.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT key, value FROM system_config")
        rows = cur.fetchall()
        conn.close()
        
        config = {row['key']: row['value'] for row in rows}
        
        return jsonify({
            "success": True,
            "form_link": config.get('form_link', ""),
            "start_date": config.get('start_date', ""),
            "end_date": config.get('end_date', ""),
            "default_reason": config.get('default_reason', "Home Visit")
        })
            
    except Exception as e:
        logging.error(f"Config fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PROFILE ROUTES
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT u.email, u.is_admin, sp.* 
            FROM users u 
            JOIN student_profiles sp ON u.id = sp.user_id 
            WHERE u.id = %s
        """, (request.user_id,))
        profile = cur.fetchone()
        conn.close()
        
        if not profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
        return jsonify({'success': True, 'profile': dict(profile)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        allowed_fields = [
            'full_name', 'student_phone', 'student_email',
            'roll_number', 'school', 'programme', 'specialization', 'academic_year',
            'parent1_name', 'parent1_email', 'parent1_phone',
            'parent2_name', 'parent2_email', 'parent2_phone'
        ]
        
        updates = []
        values = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
        
        # Handle Signature separately
        # Handle Signature separately
        if 'signature_data' in data and data['signature_data']:
            try:
                from azure_storage_helper import upload_signature_to_azure
                sig_url = upload_signature_to_azure(data['signature_data'], request.user_id)
                updates.append("signature_data = %s")
                values.append(sig_url)
                logging.info(f"Signature uploaded to Azure for user {request.user_id}: {sig_url}")
            except Exception as e:
                logging.error(f"Failed to upload signature to Azure: {e}")
                # Fallback: store base64 directly in DB
                updates.append("signature_data = %s")
                values.append(data['signature_data'])
                logging.info(f"Fallback: stored signature base64 in DB for user {request.user_id}")

        if updates:
            values.append(request.user_id)
            cur.execute(f"UPDATE student_profiles SET {', '.join(updates)} WHERE user_id = %s", values)
            
        # Handle Outlook Password Update (in users table)
        if 'outlook_password' in data and data['outlook_password']:
            try:
                new_encrypted = encrypt_outlook_password(data['outlook_password'])
                cur.execute(
                    "UPDATE users SET outlook_password_encrypted = %s WHERE id = %s",
                    (new_encrypted, request.user_id)
                )
            except Exception as e:
                logging.error(f"Failed to update outlook password: {e}")
                return jsonify({'success': False, 'error': "Failed to update password"}), 500

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Profile updated successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/reverify-credentials', methods=['POST'])
@login_required
def reverify_credentials():
    """
    Re-verify and re-encrypt Outlook credentials when decryption fails.
    Used for graceful recovery from encryption key changes.
    """
    try:
        data = request.json
        outlook_password = data.get('outlook_password')
        
        if not outlook_password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Get user email
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT email FROM users WHERE id = %s", (request.user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify credentials with Microsoft
        logging.info(f"Re-verifying Outlook credentials for {user['email']}")
        is_valid, error_msg = verify_outlook_credentials(user['email'], outlook_password)
        
        if not is_valid:
            return jsonify({
                'success': False, 
                'error': error_msg or 'Invalid Outlook credentials'
            }), 401
        
        # Re-encrypt with new stable key
        new_encrypted = encrypt_outlook_password(outlook_password)
        cur.execute(
            "UPDATE users SET outlook_password_encrypted = %s WHERE id = %s",
            (new_encrypted, request.user_id)
        )
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully re-encrypted credentials for user {request.user_id}")
        return jsonify({
            'success': True, 
            'message': 'Credentials verified and updated successfully'
        }), 200
        
    except Exception as e:
        logging.error(f"Reverify credentials error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/signatures/<path:filename>')
def serve_signature(filename):
    from flask import send_from_directory
    return send_from_directory(os.path.abspath('signatures'), filename)


# ============================================================================
# PDF GENERATION (PROTECTED)
# ============================================================================

from create_pdf import generate_parent_consent_pdf

def generate_outing_pdf_buffer(profile, start_date, end_date, reason):
    """Helper to generate PDF bytes with user details and signature using new layout"""
    try:
        import io
        
        buffer = io.BytesIO()
        
        # safely get student name/details
        student_name = profile.get('full_name') or profile.get('student_name', '')
        
        # Prepare data dict for the new generator
        # Map 'parent1' and 'parent2' from existing DB schema to what PDF needs
        pdf_data = {
            "student_name": student_name,
            "student_id": profile.get('roll_number', ''),
            "roll_number": profile.get('roll_number', ''),
            "programme": profile.get('programme', ''),
            "specialization": profile.get('specialization', ''),
            "academic_year": profile.get('academic_year', '2024-25'),
            
            # Parent details - prioritize 'parent1' keys if they exist in DB profile
            "parent_name": profile.get('parent1_name') or profile.get('parent_name', ''), 
            "parent_phone": profile.get('parent1_phone') or profile.get('parent_phone', ''),
            "parent_email": profile.get('parent1_email') or profile.get('parent_email', ''),
            
            # Specific table fields - Father/Parent1
            "father_name": profile.get('parent1_name') or profile.get('father_name', ''),
            "father_email": profile.get('parent1_email', ''),
            "father_phone": profile.get('parent1_phone', ''),
            
            # Mother/Parent2
            "mother_name": profile.get('parent2_name') or profile.get('mother_name', ''),
            "mother_email": profile.get('parent2_email', ''),
            "mother_phone": profile.get('parent2_phone', ''),
            
            # Outing Details
            "leave_start_date": start_date,
            "leave_end_date": end_date,
            "leave_date_text": start_date, # approximate
            "return_date_text": end_date, # approximate
            "reason": reason,
            "purpose": reason,
            
            # Student details for table
            "student_email": profile.get('student_email') or profile.get('email', ''),
            "student_phone": profile.get('student_phone', ''),

            # Date of generation
            "date": get_ist_now().strftime('%d-%m-%Y'),
        }
        
        # Handle signature path logic
        if profile.get('signature_path'):
             # Try absolute path first if it exists
            sig_path = profile['signature_path']
            if os.path.exists(sig_path):
                 pdf_data['signature_path'] = sig_path
            else:
                 # Check relative to CWD
                 abs_sig_path = os.path.abspath(sig_path)
                 if os.path.exists(abs_sig_path):
                     pdf_data['signature_path'] = abs_sig_path
        
        # Also pass signature_data if available (Azure URL or base64)
        if profile.get('signature_data'):
            pdf_data['signature_data'] = profile['signature_data']

        generate_parent_consent_pdf(buffer, pdf_data)
        
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"PDF Generation Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None
        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Student Signature:")
        
        sig_data = profile.get('signature_data')
        if sig_data:
            try:
                if sig_data.startswith('data:image'):
                    # Extract base64 data
                    header, encoded = sig_data.split(',', 1)
                    sig_bytes = base64.b64decode(encoded)
                    sig_image = ImageReader(io.BytesIO(sig_bytes))
                    c.drawImage(sig_image, 70, y - 60, width=100, height=50, preserveAspectRatio=True)
                elif sig_data.startswith('http://') or sig_data.startswith('https://'):
                    # Azure Blob Storage URL — download and embed
                    import urllib.request
                    sig_response = urllib.request.urlopen(sig_data)
                    sig_image = ImageReader(io.BytesIO(sig_response.read()))
                    c.drawImage(sig_image, 70, y - 60, width=100, height=50, preserveAspectRatio=True)
                else:
                    # Assume it's a file path (relative to api.py or absolute)
                    # Check relative to current working directory first
                    if os.path.exists(sig_data):
                        c.drawImage(sig_data, 70, y - 60, width=100, height=50, preserveAspectRatio=True)
                    elif os.path.exists(os.path.join(os.getcwd(), sig_data)):
                         c.drawImage(os.path.join(os.getcwd(), sig_data), 70, y - 60, width=100, height=50, preserveAspectRatio=True)
                    else:
                        c.drawString(70, y - 20, "[Signature File Not Found]")
                        logging.warning(f"Signature file not found: {sig_data}")

            except Exception as e:
                c.drawString(70, y - 20, "[Signature Error]")
                logging.error(f"Failed to draw signature: {e}")
        else:
            c.drawString(70, y - 20, "[No signature uploaded]")
        
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logging.error(f"PDF Gen Helper Error: {e}")
        return None

@app.route('/api/generate-pdf', methods=['POST'])
@login_required
def generate_pdf():
    """Generate a PDF consent form with user's stored data"""
    try:
        # Get user profile
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM v_user_profiles WHERE user_id = %s", (request.user_id,))
        profile = cur.fetchone()
        conn.close()
        
        if not profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
        
        start_date = request.json.get('start_date') if request.json else None
        end_date = request.json.get('end_date') if request.json else None
        reason = request.json.get('reason') if request.json else None
        
        pdf_buffer = generate_outing_pdf_buffer(profile, start_date, end_date, reason)
        if not pdf_buffer:
             return jsonify({'success': False, 'error': 'Failed to generate PDF'}), 500

        from flask import send_file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"outing_consent_{profile.get('roll_number', 'form')}.pdf"
        )
        
    except Exception as e:
        logging.error(f"PDF Generation Route Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# FORM SUBMISSION (PROTECTED)
# ============================================================================

@app.route('/api/admin/sync-config-from-mail', methods=['POST'])
@admin_required
def sync_config_from_mail():
    """Fetch latest email, parse config, and update DB"""
    if not get_latest_email_content:
        return jsonify({'success': False, 'error': 'Gmail service not available'}), 503

    try:
        # Search for emails from campusouting.go OR self (rajavreddy.g) OR student.outing@woxsen.edu.in
        # Note: get_latest_email_content takes a query string now, not just an email
        SENDER_QUERY = "from:campusouting.go@gmail.com OR from:rajavreddy.g@gmail.com OR from:student.outing@woxsen.edu.in OR from:me"
        print(f"DEBUG: Fetching email matching '{SENDER_QUERY}' for config sync...", flush=True)
        email_data = get_latest_email_content(SENDER_QUERY)
        
        if not email_data:
            return jsonify({'success': False, 'error': 'No relevant email found'}), 404

        # Extraction Logic (Ported from bridge.py)
        form_link = None
        if email_data.get('form_links'):
            form_link = email_data['form_links'][0]

        combined_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        
        # Regex for Date (DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY)
        import re
        # Matches dd.mm.yyyy, dd/mm/yyyy, or dd-mm-yyyy
        date_pattern = re.compile(r'\b(\d{2}[./-]\d{2}[./-]\d{4})\b')
        match = date_pattern.search(combined_text)
        start_date = match.group(1) if match else None
        
        end_date = None
        reason = None

        # Calculate End Date if Start Date found
        if start_date:
            try:
                # Normalize separator to dot for strptime if needed, or handle variations
                # actually strptime requires specific format. Let's try to detect or normalize.
                clean_date = start_date.replace('/', '.').replace('-', '.')
                start_obj = datetime.strptime(clean_date, "%d.%m.%Y")
                end_obj = start_obj + timedelta(days=2)
                end_date = end_obj.strftime("%d.%m.%Y")
                # Convert to YYYY-MM-DD for DB/Frontend consistency if needed, 
                # but system_config seems to store what bridge.py sends.
                # Let's standardize on YYYY-MM-DD for the frontend inputs
                start_date = start_obj.strftime("%Y-%m-%d")
                end_date = end_obj.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Date parse error: {e}")

        # Grok Fallback
        if (not form_link or not start_date or not reason) and process_content_with_groq:
            print("DEBUG: Using Grok for fallback/enrichment...", flush=True)
            try:
                grok_result = process_content_with_groq(email_data)
                if grok_result:
                    if not start_date and grok_result.get('start_date'):
                        # Grok usually returns DD.MM.YYYY based on prompt, verify and convert
                        sd_raw = grok_result['start_date']
                        try:
                            s_obj = datetime.strptime(sd_raw, "%d.%m.%Y")
                            start_date = s_obj.strftime("%Y-%m-%d")
                            end_date = (s_obj + timedelta(days=2)).strftime("%Y-%m-%d")
                        except:
                            # Try YYYY-MM-DD just in case
                            try:
                                s_obj = datetime.strptime(sd_raw, "%Y-%m-%d")
                                start_date = s_obj.strftime("%Y-%m-%d")
                                end_date = (s_obj + timedelta(days=2)).strftime("%Y-%m-%d")
                            except:
                                pass

                    if not form_link and grok_result.get('form_link'):
                        form_link = grok_result['form_link']
                    if not reason and grok_result.get('reason'):
                        reason = grok_result['reason']
            except Exception as e:
                print(f"Grok fallback failed: {e}")

        # Defaults if still missing
        if not reason: reason = "Home Visit"

        # Update Database
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = {}
        if form_link: updates['form_link'] = form_link
        if start_date: updates['start_date'] = start_date
        if end_date: updates['end_date'] = end_date
        if reason: updates['default_reason'] = reason
        
        for key, value in updates.items():
            cur.execute("""
                INSERT INTO system_config (key, value, updated_at) 
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
            """, (key, value))
            
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Config updated from email',
            'updates': updates
        }), 200

    except Exception as e:
        print(f"Sync Config Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/submit-form', methods=['POST'])
@login_required
def submit_form():
    """
    Submit form with auto-generated PDF
    Accepts JSON: {form_url, leave_start_date, leave_end_date, reason}
    """
    conn = None
    try:

        # 1. Get Data (Handle both JSON and Multipart/FormData)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle key-value from FormData or JSON string in 'data' field
            if 'data' in request.form:
                import json
                try:
                    request_data = json.loads(request.form['data'])
                except:
                    return jsonify({'success': False, 'error': 'Invalid JSON in "data" field'}), 400
            else:
                # Try to get fields directly from form (fallback)
                request_data = request.form.to_dict()
        else:
            # Standard JSON request
            request_data = request.json

        if not request_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        form_url = request_data.get('form_url')
        leave_start_date = request_data.get('leave_start_date')  # YYYY-MM-DD
        leave_end_date = request_data.get('leave_end_date')      # YYYY-MM-DD
        reason = request_data.get('reason')
        
        if not form_url:
            return jsonify({'success': False, 'error': 'Form URL is required'}), 400
        if not leave_start_date or not leave_end_date:
            return jsonify({'success': False, 'error': 'Start and end dates are required'}), 400

        # 2. Retrieve User Credentials & Profile from DB
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get auth/credentials
        cur.execute(
            "SELECT email, outlook_password_encrypted FROM users WHERE id = %s",
            (request.user_id,)
        )
        user_auth = cur.fetchone()
        
        # Get profile data
        cur.execute(
            "SELECT * FROM student_profiles WHERE user_id = %s",
            (request.user_id,)
        )
        profile = cur.fetchone()
        
        if not user_auth or not profile:
            return jsonify({'success': False, 'error': 'User profile incomplete or missing'}), 404
            
        # Decrypt password
        try:
            outlook_password = decrypt_outlook_password(user_auth['outlook_password_encrypted'])
        except Exception as e:
            logging.warning(f"Decryption failed for user {request.user_id}: {e}")
            return jsonify({
                'success': False, 
                'error': 'Failed to decrypt credentials. Please re-verify your password.',
                'error_code': 'CREDENTIAL_REVERIFY_NEEDED'
            }), 400
        
        # 3. Get PDF (Prefer Uploaded File > Generate New)
        pdf_buffer = None
        
        # Check if file was uploaded
        if 'pdf' in request.files:
            uploaded_file = request.files['pdf']
            if uploaded_file.filename != '':
                logging.info(f"Using uploaded PDF: {uploaded_file.filename}")
                pdf_buffer = uploaded_file.read()

        # If no file uploaded, generate one (Fallback)
        if not pdf_buffer:
            logging.info(f"No PDF uploaded. Generating new PDF for user {request.user_id}...")
            # Merge profile with user email for PDF generation
            profile_data = dict(profile)
            profile_data['email'] = user_auth['email']
            
            pdf_buffer = generate_outing_pdf_buffer(profile_data, leave_start_date, leave_end_date, reason)
            
        if not pdf_buffer:
            return jsonify({'success': False, 'error': 'Failed to provide or generate PDF'}), 500
        
        # 4. Upload PDF to Azure Blob Storage
        try:
            from azure_storage_helper import upload_to_azure_blob
            
            filename = f"outing_{request.user_id}_{get_ist_now().strftime('%Y%m%d%H%M%S')}.pdf"
            upload_result = upload_to_azure_blob(pdf_buffer, filename)
            
            blob_name = upload_result['blob_name']
            pdf_url = upload_result['public_url']
            
            logging.info(f"PDF uploaded to Azure: {blob_name}")
            
        except Exception as e:
            logging.error(f"Azure upload failed: {e}")
            return jsonify({'success': False, 'error': f'Failed to upload PDF to cloud: {str(e)}'}), 500
            
        # 5. Prepare Automation Data
        # Convert YYYY-MM-DD to DD.MM.YYYY for form compatibility
        def format_date_for_form(date_str):
            """Convert YYYY-MM-DD to M/d/yyyy for Microsoft Forms"""
            if not date_str: return ''
            try:
                parts = date_str.split('-')  # YYYY-MM-DD
                if len(parts) == 3:
                    year = parts[0]
                    month = str(int(parts[1]))   # Remove leading zero: 02 -> 2
                    day = str(int(parts[2]))     # Remove leading zero: 05 -> 5
                    return f"{month}/{day}/{year}"  # M/d/yyyy format
                return date_str
            except:
                return date_str
        
        # Normalize programme to handle stale DB values (e.g., "BBA" should be "B.Tech")
        def normalize_programme(prog):
            if not prog: return ''
            norm = ''.join(c for c in prog if c.isalnum()).lower()
            if 'btech' in norm or 'technology' in norm or 'engineering' in norm:
                return 'B.Tech'
            STANDARD = ["B.Tech","BBA","BCom","B.Sc","B.Des","B.Arch",
                        "Integrated MBA","Integrated BBA-MBA","MBA",
                        "MBA (BA/AI/ML)","MBA (Financial Services)"]
            for s in STANDARD:
                sn = ''.join(c for c in s if c.isalnum()).lower()
                if norm == sn:
                    return s
            return prog
        
        form_data = {
            'student_name': profile['full_name'],
            'roll_number': profile['roll_number'],
            'school': profile['school'],
            'academic_session': profile['academic_year'],
            'programme': normalize_programme(profile['programme']),
            'specialization': profile['specialization'],
            'student_phone': profile['student_phone'],
            # CHANGED: Do NOT fallback to admin email. Use student email or empty string.
            'student_email': profile['student_email'] or '',
            'parent_name': profile['parent1_name'],
            'parent_phone': profile['parent1_phone'],
            'parent_email': profile['parent1_email'],
            'parent2_name': profile.get('parent2_name'),
            'parent2_phone': profile.get('parent2_phone'),
            'reason': reason,
            'leave_start_date': format_date_for_form(leave_start_date),
            'leave_end_date': format_date_for_form(leave_end_date)
        }

        # 6. Create Task & Log to DB
        task_id = f"task_{request.user_id}_{get_ist_now().strftime('%Y%m%d_%H%M%S')}"
        task = AutomationTask(task_id, request.user_id)
        automation_tasks[task_id] = task
        
        # Store blob_name in task for later deletion
        task.blob_name = blob_name
        
        cur.execute(
            """
            INSERT INTO submission_history 
            (user_id, task_id, form_url, leave_start_date, leave_end_date, status, pdf_path, ip_address, form_data, blob_name)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s, %s)
            """,
            (
                request.user_id, task_id, form_url,
                leave_start_date, leave_end_date,
                pdf_url,  # Store Azure URL instead of local path
                request.remote_addr,
                psycopg2.extras.Json(form_data),
                blob_name
            )
        )
        
        # Log activity
        cur.execute(
            "INSERT INTO activity_logs (user_id, action, description) VALUES (%s, 'submission_started', 'Started form automation')",
            (request.user_id,)
        )
        conn.commit()
        
        # 7. Add to Queue for Scalable Automation
        task_payload = {
            'task_id': task_id,
            'user_id': request.user_id,
            'form_url': form_url,
            'email': user_auth['email'],
            'password': outlook_password,
            'form_data': form_data,
            'pdf_path': pdf_url,
            'blob_name': blob_name
        }
        
        # This will be picked up by the automation_worker thread
        automation_queue.put(task_payload)

        # Update status in DB to 'queued' now that it's in the queue
        cur.execute(
            "UPDATE submission_history SET status = 'queued' WHERE task_id = %s",
            (task_id,)
        )
        conn.commit()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task queued. We will process it shortly.',
            'queue_position': automation_queue.qsize()  # Initial position
        }), 202
        
    except Exception as e:
        logging.error(f"Error starting automation: {str(e)}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/live-view/<task_id>')
def task_live_view(task_id):
    """Return an HTML page that shows the latest screenshot for a task"""
    task = automation_tasks.get(task_id)
    if not task:
        return "Task not found", 404
        
    html = f"""
    <html>
        <head>
            <title>Live Automation View</title>
            <meta http-equiv="refresh" content="3">
            <style>
                body {{ background: #1a1a1a; color: white; font-family: sans-serif; text-align: center; margin: 0; padding: 10px; }}
                .container {{ max-width: 1000px; margin: auto; }}
                img {{ width: 100%; border-radius: 8px; border: 2px solid #444; }}
                .status {{ margin: 10px 0; font-size: 1.2rem; }}
                .progress-bar {{ background: #333; height: 10px; border-radius: 5px; overflow: hidden; margin: 10px 0; }}
                .progress-fill {{ background: #00ff00; height: 100%; width: {task.progress}%; transition: width 0.3s; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="status">🤖 <b>Status:</b> {task.message}</div>
                <div class="progress-bar"><div class="progress-fill"></div></div>
                {f'<img src="{task.screenshot_path}">' if task.screenshot_path else '<p>Waiting for first screenshot...</p>'}
            </div>
        </body>
    </html>
    """
    return html

@app.route('/api/task-status/<task_id>', methods=['GET'])
@login_required # Optional: restrict to task owner?
def get_task_status(task_id):
    # Check DB first (Source of Truth for worker updates)
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM submission_history WHERE task_id = %s", (task_id,))
        task = cur.fetchone()
        conn.close()
        
        if task:
             return jsonify({'success': True, 'task': dict(task)})
    except:
        pass

    # Check memory secondary (for very fresh tasks not yet committed?)
    if task_id in automation_tasks:
        return jsonify({'success': True, 'task': automation_tasks[task_id].to_dict()})
        
    return jsonify({'success': False, 'error': 'Task not found'}), 404
    
@app.route('/api/submissions', methods=['GET'])
@login_required
def get_history():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM submission_history WHERE user_id = %s ORDER BY submitted_at DESC LIMIT 20",
            (request.user_id,)
        )
        history = cur.fetchall()
        conn.close()
        return jsonify({'success': True, 'submissions': [dict(h) for h in history]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PAYMENT & SUBSCRIPTION CONFIGURATION
# ============================================================================

# Payment Gateway Setup
# Payment Gateway Setup
# Use Environment Variables from Azure/Service
razorpay_key_id = os.getenv('RAZORPAY_KEY_ID')
razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET')

print(f"DEBUG: Initializing Razorpay with Key ID: {razorpay_key_id}", flush=True)
razorpay_client = razorpay.Client(
    auth=(razorpay_key_id, razorpay_key_secret)
)



# Admin credentials
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'campusouting.go@gmail.com')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', '$2b$12$W0VJrQxqHdmO.oSjbUky/e.YuinwnSi4JovaTbTskk.ohVqNvUVv82')

# Subscription Plans (NO FREE PLAN)
SUBSCRIPTION_PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'price': 50,
        'currency': 'INR',
        'duration_days': 30, # Monthly
        'features': {
            'monthly_submissions': 999, # Unlimited (at least 4)
            'auto_submit': True,
            'email_notifications': True,
            'sms_notifications': False,
            'priority_support': False,
            'data_backup': True
        }
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 180,
        'currency': 'INR',
        'duration_days': 120, # 4 Months
        'features': {
            'monthly_submissions': 9999,
            'auto_submit': True,
            'email_notifications': True,
            'sms_notifications': True,
            'priority_support': True,
            'data_backup': True
        }
    }
}

# ============================================================================
# ADMIN AUTHENTICATION DECORATOR
# ============================================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token: return jsonify({'success': False, 'error': 'No authorization'}), 401
        if token.startswith('Bearer '): token = token[7:]
        
        payload = verify_jwt(token)
        if not payload: return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT email, is_admin FROM users WHERE id = %s', (payload['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        request.user_id = payload['user_id']
        request.is_admin = True
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# SUBSCRIPTION ROUTES
# ============================================================================

@app.route('/api/subscription/plans', methods=['GET'])
def get_plans():
    return jsonify({'success': True, 'plans': SUBSCRIPTION_PLANS})

@app.route('/api/subscription/current', methods=['GET'])
@login_required
def get_current_subscription():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT s.*,
                CASE 
                    WHEN s.subscription_end IS NULL THEN NULL
                    WHEN s.subscription_end < CURRENT_DATE THEN 'expired'
                    WHEN s.subscription_end < CURRENT_DATE + INTERVAL '7 days' THEN 'expiring_soon'
                    ELSE 'active'
                END as subscription_status
            FROM subscriptions s WHERE user_id = %s
        """, (request.user_id,))
        subscription = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'subscription': subscription})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    try:
        data = request.json
        plan_type = data.get('plan_type')
        # Force Razorpay
        gateway = 'razorpay'
        
        if plan_type not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'error': 'Invalid plan type'}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_type]
        amount = plan['price']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        print("DEBUG: DB Connection established", flush=True)
        
        # Razorpay only
        order_data = {
            'amount': amount * 100,
            'currency': plan['currency'],
            'payment_capture': 1,
            'notes': {'user_id': request.user_id, 'plan_type': plan_type}
        }
        print(f"DEBUG: Creating Razorpay order with data: {order_data}", flush=True)
        
        # Retry logic for Razorpay connection issues
        import time
        max_retries = 3
        order = None
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                order = razorpay_client.order.create(data=order_data)
                print(f"DEBUG: Razorpay Order created: {order}", flush=True)
                break
            except Exception as e:
                print(f"DEBUG: Razorpay Create Failed (Attempt {attempt+1}/{max_retries}): {e}", flush=True)
                last_exception = e
                time.sleep(1) # Wait 1 second before retrying
        
        if not order:
             print(f"DEBUG: Razorpay Create Failed after {max_retries} attempts: {last_exception}", flush=True)
             return jsonify({'success': False, 'error': f"Razorpay connection failed: {str(last_exception)}"}), 500
        
        print("DEBUG: Inserting payment into DB...", flush=True)
        cur.execute("""
            INSERT INTO payments (user_id, plan_type, amount, currency, payment_gateway, payment_order_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending') RETURNING id
        """, (request.user_id, plan_type, amount, plan['currency'], 'razorpay', order['id']))
        
        result = cur.fetchone()
        payment_id = result['id'] if result else None
        print(f"DEBUG: Payment inserted with ID: {payment_id}", flush=True)
        
        conn.commit()
        print("DEBUG: DB Commit successful", flush=True)
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'gateway': 'razorpay',
            'order_id': order['id'],
            'amount': amount,
            'currency': plan['currency'],
            'key': razorpay_key_id # Use the global variable we set
        })
            
    except Exception as e:
        print(f"Upgrade Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
            




@app.route('/api/subscription/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    print("DEBUG: /verify-payment called", flush=True)
    try:
        data = request.json
        print(f"DEBUG: Verify Data: {data}", flush=True)
        
        try:
            print("DEBUG: Verifying signature...", flush=True)
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })
            print("DEBUG: Signature Verified!", flush=True)
        except Exception as sig_err:
            print(f"DEBUG: Signature Verification Failed: {sig_err}", flush=True)
            return jsonify({'success': False, 'error': f'Invalid signature: {str(sig_err)}'}), 400
            
        print("DEBUG: Connecting to DB...", flush=True)
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT * FROM payments WHERE payment_order_id = %s", (data['razorpay_order_id'],))
        payment = cur.fetchone()
        
        if not payment: 
            print("DEBUG: Payment order not found in DB", flush=True)
            return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        print(f"DEBUG: Found payment record: {payment['id']}", flush=True)
        plan = SUBSCRIPTION_PLANS[payment['plan_type']]
        sub_end = datetime.now() + timedelta(days=plan['duration_days'])
        
        print("DEBUG: Updating payment status...", flush=True)
        cur.execute("UPDATE payments SET status = 'completed', payment_id = %s, completed_at = NOW() WHERE id = %s",
                   (data['razorpay_payment_id'], payment['id']))
                   
        print("DEBUG: Updating subscription...", flush=True)
        cur.execute("""
            UPDATE subscriptions SET 
                plan_type = %s,
                is_auto_submit = %s,
                monthly_submissions_limit = %s,
                subscription_start = CURRENT_DATE,
                subscription_end = %s
            WHERE user_id = %s
        """, (payment['plan_type'], plan['features']['auto_submit'], plan['features']['monthly_submissions'], sub_end, request.user_id))
        
        cur.execute("INSERT INTO activity_logs (user_id, action, description) VALUES (%s, 'subscription_upgrade', %s)",
                   (request.user_id, f"Upgraded to {plan['name']}"))
                   
        conn.commit()
        cur.close()
        conn.close()
        print("DEBUG: Upgrade Successful!", flush=True)
        return jsonify({'success': True, 'message': 'Upgraded!'})
    except Exception as e:
        print(f"DEBUG: Verify Critical Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f"Server Error: {str(e)}"}), 500

# Admin Routes are consolidated above around line 600.
# The following section was redundant and has been removed.



# ============================================================================
# HEALTH CHECK (FOR RAILWAY/DOCKER)
# ============================================================================

# Track last recovery info for health check
_last_recovery_error = None
_last_recovery_time = None
_recovery_count = 0

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway/Docker deployment monitoring"""
    try:
        # Test database connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check if worker thread is alive
    worker_status = "running" if worker_thread.is_alive() else "dead"

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'worker_thread': worker_status,
        'timestamp': format_ist_timestamp(),
        'queue_size': automation_queue.qsize(),
        'last_recovery_error': _last_recovery_error,
        'last_recovery_time': _last_recovery_time,
        'recovery_count': _recovery_count,
        'api_file': __file__,
        'version': 'v9-status-fix'
    })

@app.route('/api/admin/recover', methods=['POST'])
def manual_recover():
    """Manually trigger task recovery."""
    try:
        recover_pending_tasks()
        return jsonify({'success': True, 'msg': 'Recovery triggered', 'queue_size': automation_queue.qsize()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/diagnose', methods=['GET'])
def diagnostic_check():
    """Check worker health and queue status."""
    global _last_recovery_error, worker_thread
    status = {
        'queue_size': automation_queue.qsize(),
        'worker_alive': worker_thread.is_alive(),
        'last_error': _last_recovery_error,
        'tasks_in_memory': len(automation_tasks),
        'db_connection': 'unknown'
    }
    
    # Test DB connection
    try:
        conn = get_db_connection()
        conn.close()
        status['db_connection'] = 'ok'
    except Exception as e:
        status['db_connection'] = str(e)
        
    return jsonify(status)
    
@app.route('/api/admin/env', methods=['GET'])
def diagnostic_env():
    """Sanitized env dump for debugging"""
    return jsonify({
        'DB_HOST': os.getenv('DB_HOST'),
        'DB_NAME': os.getenv('DB_NAME'),
        'DB_USER': os.getenv('DB_USER'),
        'PORT': os.getenv('PORT'),
        'PYTHONPATH': os.getenv('PYTHONPATH'),
        'api_dir': os.path.dirname(os.path.abspath(__file__)),
        'cwd': os.getcwd(),
        'pip_list': [],
        'requirements_txt': ''
    })
    
    try:
        import subprocess
        data['pip_list'] = subprocess.check_output([sys.executable, '-m', 'pip', 'list']).decode().split('\n')
        req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                data['requirements_txt'] = f.read()
    except Exception as e:
        data['error'] = str(e)
        
    return jsonify(data)

@app.route('/api/admin/worker-log', methods=['GET'])
def get_worker_log():
    """Get the last N lines of the worker log + Debug Info."""
    try:
        api_dir = os.path.dirname(os.path.abspath(__file__))
        # Allow choosing which log to read
        log_type = request.args.get('file', 'worker')
        if log_type == 'main':
            log_file = os.path.join(api_dir, 'automation.log')
        else:
            log_file = os.path.join(api_dir, 'automation_worker.log')

        lines = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-200:]
        else:
            lines = ["Log file not found"]
            
        debug_info = {
            'api_dir': api_dir,
            'cwd': os.getcwd(),
            'sys.path': sys.path
        }
            
        return jsonify({'success': True, 'log': lines, 'debug': debug_info})
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

def recover_pending_tasks():
    """
    On startup, check DB for 'pending' tasks and re-queue them.
    This handles cases where the app restarted (clearing memory queue) but tasks weren't processed.
    """
    global _last_recovery_error, _last_recovery_time, _recovery_count
    try:
        _last_recovery_time = format_ist_timestamp()
        _recovery_count += 1
        print("RECOVERY: Checking for pending detailed tasks...", flush=True)
        conn = get_db_connection()
        print("RECOVERY: Got DB connection", flush=True)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # We need to join with users to get credentials (email, password)
        # We also need form_data which we just added to schema
        query = """
            SELECT s.*, u.email, u.outlook_password_encrypted 
            FROM submission_history s
            JOIN users u ON s.user_id = u.id
            WHERE s.status = 'pending'
        """
        print(f"RECOVERY: Executing query: {query}", flush=True)
        cur.execute(query)
        pending_tasks = cur.fetchall()
        print(f"RECOVERY: Found {len(pending_tasks)} pending tasks via JOIN", flush=True)
        
        # Diagnostic: check without JOIN if join returned 0
        if len(pending_tasks) == 0:
            cur.execute("SELECT count(*) FROM submission_history WHERE status IN ('pending', 'queued')")
            raw_count = cur.fetchone()['count']
            print(f"RECOVERY DIAGNOSTIC: Found {raw_count} tasks in submission_history WITHOUT join", flush=True)
            
        cur.close()
        conn.close()
        
        count = 0
        for row in pending_tasks:
            try:
                # Decrypt password
                password = decrypt_outlook_password(row['outlook_password_encrypted'])
                
                # Reconstruct payload
                # Ideally, form_data is in the row (new schema)
                # If not (old tasks), we might have trouble.
                
                form_data = row.get('form_data')
                
                if not form_data:
                    # Fallback for old tasks without stored form_data:
                    # We can try to reconstruct it from profile if we really want,
                    # but 'reason' is missing. 
                    # For now, skip or log warning.
                    print(f"RECOVERY WARNING: Task {row['task_id']} has no saved form_data. Skipping.", flush=True)
                    continue
                    
                task_payload = {
                    'task_id': row['task_id'],
                    'user_id': row['user_id'],
                    'form_url': row['form_url'],
                    'email': row['email'],
                    'password': password,
                    'form_data': form_data,
                    'pdf_path': row['pdf_path'],
                    'blob_name': row.get('blob_name')
                }
                
                # Add to queue
                automation_queue.put(task_payload)
                
                # Re-add to memory for status tracking
                if row['task_id'] not in automation_tasks:
                    task = AutomationTask(row['task_id'], row['user_id'])
                    task.status = 'pending' 
                    task.message = 'Recovered from restart'
                    automation_tasks[row['task_id']] = task
                    
                count += 1
                
            except Exception as e:
                print(f"RECOVERY ERROR for task {row.get('task_id')}: {e}", flush=True)
                
        print(f"RECOVERY: Restored {count} pending tasks to queue.", flush=True)
        
    except Exception as e:
        _last_recovery_error = str(e)
        print(f"RECOVERY: Error recovering tasks: {e}", flush=True)


@app.route('/signatures/<path:filename>')
def serve_signatures(filename):
    return send_from_directory(os.path.join(app.root_path, 'signatures'), filename)

if __name__ == '__main__':
    os.makedirs('screenshots', exist_ok=True)
    os.makedirs('temp_uploads', exist_ok=True)
    os.makedirs('signatures', exist_ok=True)
    
    # Recover tasks moved to module level for Gunicorn
    # recover_pending_tasks()
    
    # Get port from environment (Railway sets PORT)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
