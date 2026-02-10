"""
Flask API to trigger Microsoft Forms automation
Integrates with your existing PDF generation web app and PostgreSQL database
"""

import httpx
import supabase
# print(f"DEBUG: httpx version: {httpx.__version__}", flush=True)
# print(f"DEBUG: supabase version: {supabase.__version__}", flush=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import json
import os
import logging
print("DEBUG: API.PY MODULE LOADING...", flush=True)
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv
# Force override of environment variables from .env file
import os
from pathlib import Path

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

print("="*50, flush=True)
print(f"DEBUG: STARTING APP - {datetime.now().isoformat()}", flush=True)
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

def get_db_connection():
    db_host = os.getenv('DB_HOST')
    try:
        # Standard connection using hostname (Pooler is IPv4)
        conn = psycopg2.connect(
            host=db_host,
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER', 'postgres.uehkqlamchtdzcusqmhi'), # HARDCODED FIX
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            connect_timeout=10,
            sslmode='require'
        )
        print("DEBUG: DB Connection SUCCESS!", flush=True)
        return conn
    except Exception as e:
        print(f"DEBUG: DB Connection FAILED: {e}", flush=True)
        raise e

# Import the automation class (Optional for now)
# Import the automation class (Optional for now)
try:
    try:
        from form_filler.ms_form_automation import MSFormAutomation
    except ImportError:
         from ms_form_automation import MSFormAutomation
except ImportError:
    MSFormAutomation = None
    logging.warning("Playwright not installed or module not found. Automation features disabled.")

# Import authentication system (Supabase-based, no password required!)
# Import authentication system (Supabase-based, no password required!)
try:
    from form_filler.auth_system_v2 import (
        register_user, login_user, verify_email_token,
        request_password_reset, reset_password,
        encrypt_outlook_password, decrypt_outlook_password,
        hash_password, verify_outlook_credentials,
        verify_password, generate_jwt, verify_jwt,
        get_user_profile, supabase, login_required
    )
except ImportError:
    from auth_system_v2 import (
        register_user, login_user, verify_email_token,
        request_password_reset, reset_password,
        encrypt_outlook_password, decrypt_outlook_password,
        hash_password, verify_outlook_credentials,
        verify_password, generate_jwt, verify_jwt,
        get_user_profile, supabase, login_required
    )

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

@app.route('/')
def home():
    return jsonify({
        "service": "Outing Automation Backend",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "health_check": "/health"
    })
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

# Store active automation tasks
automation_tasks = {}
import queue

# Global Automation Queue for Scalability
automation_queue = queue.Queue()

@app.route('/api/config/active-outing', methods=['GET'])
def get_active_outing_config():
    """
    Get the latest outing configuration (form link, dates) 
    from the most recent automated submission.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get the very latest submission task to infer current config
        cur.execute("""
            SELECT form_url, leave_start_date, leave_end_date 
            FROM submission_history 
            WHERE form_url IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 1
        """)
        latest = cur.fetchone()
        conn.close()
        
        if latest:
            return jsonify({
                "success": True,
                "form_link": latest['form_url'],
                "start_date": latest['leave_start_date'].strftime('%Y-%m-%d') if latest['leave_start_date'] else None,
                "end_date": latest['leave_end_date'].strftime('%Y-%m-%d') if latest['leave_end_date'] else None
            })
        else:
            # Return nulls if no history exists yet
            return jsonify({
                "success": True,
                "form_link": "",
                "start_date": "",
                "end_date": ""
            })
            
    except Exception as e:
        logging.error(f"Config fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def automation_worker():
    while True:
        task_info = automation_queue.get()
        if task_info is None:
            break
            
        try:
            logging.info(f"Processing queued task: {task_info['task_id']} for user {task_info['user_id']}")
            run_automation_async(
                task_info['task_id'],
                task_info['form_url'],
                task_info['email'],
                task_info['password'],
                task_info['form_data'],
                task_info['pdf_path']
            )
        except Exception as e:
            logging.error(f"Worker failed processing task {task_info['task_id']}: {e}")
        finally:
            automation_queue.task_done()

# Start the worker thread
worker_thread = threading.Thread(target=automation_worker, daemon=True)
worker_thread.start()

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
        
        # Headless=True REQUIRED for Azure/Docker deployment (no UI available)
        automation = MSFormAutomation(headless=True) 
        
        # Run the full workflow
        success = automation.run_automation(
            form_url=form_url,
            email=email,
            password=password,
            form_data=form_data,
            pdf_path=pdf_path
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
                
        else:
            raise Exception("Automation reported failure")
        
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

        # 1. Find all eligible users (Auto-submit enabled, Active subscription)
        # We join with users table to ensure user account is valid
        cur.execute("""
            SELECT u.id, u.email, u.outlook_password_encrypted, sp.* 
            FROM users u
            JOIN subscriptions s ON u.id = s.user_id
            JOIN student_profiles sp ON u.id = sp.user_id
            WHERE s.is_auto_submit = 1 
              AND s.subscription_end >= CURRENT_DATE
              AND u.is_active = 1
        """)
        eligible_users = cur.fetchall()
        
        tasks_created = 0

        for user in eligible_users:
            try:
                user_id = user['id']

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
                pdf_path = os.path.join(temp_dir, f"auto_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
                
                # Generate PDF using helper
                pdf_buffer = create_outing_pdf(user, start_date, end_date, out_reason)
                if pdf_buffer:
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_buffer.getvalue())
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
                task_id = f"auto_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
                logging.error(f"Error preparing task for user {user.get('id')}: {u_e}")

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
        result = login_user(data.get('email'), data.get('password'))
        return jsonify(result), 200 if result['success'] else 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
# PROFILE ROUTES
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT u.email, sp.* 
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
                import base64
                import uuid
                
                sig_data = data['signature_data']
                if ',' in sig_data:
                    sig_data = sig_data.split(',')[1]
                
                sig_dir = 'signatures'
                os.makedirs(sig_dir, exist_ok=True)
                
                filename = f"sig_{request.user_id}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(sig_dir, filename)
                
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(sig_data))
                
                # Store relative path
                updates.append("signature_data = %s")
                values.append(f"signatures/{filename}")
                logging.info(f"Saved signature for user {request.user_id} at {filepath}")
            except Exception as e:
                logging.error(f"Failed to save signature: {e}")
                pass

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

@app.route('/signatures/<path:filename>')
def serve_signature(filename):
    from flask import send_from_directory
    return send_from_directory(os.path.abspath('signatures'), filename)


# ============================================================================
# PDF GENERATION (PROTECTED)
# ============================================================================

@app.route('/api/generate-pdf', methods=['POST'])
@login_required
def create_outing_pdf(profile, start_date, end_date, reason):
    """Helper to generate PDF bytes with user details and signature"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        import io
        import base64

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 50, "OUTING CONSENT FORM")
        
        # Student Details
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 100, "Student Details:")
        c.setFont("Helvetica", 11)
        y = height - 120
        details = [
            f"Name: {profile.get('full_name', '')}",
            f"Roll Number: {profile.get('roll_number', '')}",
            f"School: {profile.get('school', '')}",
            f"Programme: {profile.get('programme', '')} - {profile.get('specialization', '')}",
            f"Academic Year: {profile.get('academic_year', '')}",
            f"Student Phone: {profile.get('student_phone', '')}",
            f"Student Email: {profile.get('email', '')}",
        ]
        for detail in details:
            c.drawString(70, y, detail)
            y -= 18
        
        # Date & Reason Details
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Outing Details:")
        c.setFont("Helvetica", 11)
        y -= 20
        c.drawString(70, y, f"Start Date: {start_date or 'To be filled'}")
        y -= 18
        c.drawString(70, y, f"End Date: {end_date or 'To be filled'}")
        y -= 18
        c.drawString(70, y, f"Reason: {reason or 'Home Visit'}")
        
        # Parent Details
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Father's Details:")
        c.setFont("Helvetica", 11)
        y -= 20
        c.drawString(70, y, f"Name: {profile.get('parent1_name', '')}")
        y -= 18
        c.drawString(70, y, f"Email: {profile.get('parent1_email', '')}")
        y -= 18
        c.drawString(70, y, f"Phone: {profile.get('parent1_phone', '')}")
        
        # Mother Details (if available)
        y -= 30
        if profile.get('parent2_name'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Mother's Details:")
            c.setFont("Helvetica", 11)
            y -= 20
            c.drawString(70, y, f"Name: {profile.get('parent2_name', '')}")
            y -= 18
            c.drawString(70, y, f"Email: {profile.get('parent2_email', '')}")
            y -= 18
            c.drawString(70, y, f"Phone: {profile.get('parent2_phone', '')}")
        
        # Signature
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
        
        pdf_buffer = create_outing_pdf(profile, start_date, end_date, reason)
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

@app.route('/api/submit-form', methods=['POST'])
@login_required
def submit_form():
    """
    Submit form with auto-generated PDF
    Accepts JSON: {form_url, leave_start_date, leave_end_date, reason}
    """
    conn = None
    try:
        # 1. Get JSON data
        request_data = request.json
        if not request_data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
            
        form_url = request_data.get('form_url')
        leave_start_date = request_data.get('leave_start_date')  # YYYY-MM-DD
        leave_end_date = request_data.get('leave_end_date')      # YYYY-MM-DD
        reason = request_data.get('reason', 'Home Visit')
        
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
            return jsonify({'success': False, 'error': 'Failed to decrypt credentials. Please update your password.'}), 400
        
        # 3. Generate PDF with provided dates and reason
        logging.info(f"Generating PDF for user {request.user_id} with dates {leave_start_date} to {leave_end_date}")
        
        # Merge profile with user email for PDF generation
        profile_data = dict(profile)
        profile_data['email'] = user_auth['email']
        
        pdf_buffer = create_outing_pdf(profile_data, leave_start_date, leave_end_date, reason)
        if not pdf_buffer:
            return jsonify({'success': False, 'error': 'Failed to generate PDF'}), 500
        
        # 4. Upload PDF to Azure Blob Storage
        try:
            from azure_storage_helper import upload_to_azure_blob
            
            filename = f"outing_{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
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
            if not date_str: return ''
            try:
                parts = date_str.split('-')  # YYYY-MM-DD
                if len(parts) == 3:
                    return f"{parts[2]}.{parts[1]}.{parts[0]}"  # DD.MM.YYYY
                return date_str
            except:
                return date_str
        
        form_data = {
            'student_name': profile['full_name'],
            'roll_number': profile['roll_number'],
            'school': profile['school'],
            'academic_session': profile['academic_year'],
            'programme': profile['programme'],
            'specialization': profile['specialization'],
            'student_phone': profile['student_phone'],
            'student_email': profile['student_email'] or user_auth['email'],
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
        task_id = f"task_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = AutomationTask(task_id, request.user_id)
        automation_tasks[task_id] = task
        
        # Store blob_name in task for later deletion
        task.blob_name = blob_name
        
        cur.execute(
            """
            INSERT INTO submission_history 
            (user_id, task_id, form_url, leave_start_date, leave_end_date, status, pdf_path, ip_address)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s)
            """,
            (
                request.user_id, task_id, form_url,
                leave_start_date, leave_end_date,
                pdf_url,  # Store Azure URL instead of local path
                request.remote_addr
            )
        )
        
        # Log activity
        cur.execute(
            "INSERT INTO activity_logs (user_id, action, description) VALUES (%s, 'submission_started', 'Started form automation')",
            (request.user_id,)
        )
        conn.commit()
        
        # 7. Start Async Automation
        thread = threading.Thread(
            target=run_automation_async,
            args=(
                task_id,
                form_url,
                user_auth['email'],
                outlook_password,
                form_data,
                pdf_url,  # Pass Azure URL instead of local path
                blob_name  # Pass blob name for cleanup
            )
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Automation started successfully'
        }), 202
        
    except Exception as e:
        logging.error(f"Error starting automation: {str(e)}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/task-status/<task_id>', methods=['GET'])
@login_required # Optional: restrict to task owner?
def get_task_status(task_id):
    # Check memory first
    if task_id in automation_tasks:
        return jsonify({'success': True, 'task': automation_tasks[task_id].to_dict()})
        
    # Check DB if not in memory (for history)
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

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/api/admin/login', methods=['POST'])
def admin_login_route():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        print(f"Admin Login Attempt: {email}") # Debug
        
        if email != ADMIN_EMAIL:
            return jsonify({'success': False, 'error': 'Invalid admin email'}), 401
        
        # Direct password check for admin (temporary fix for hash storage issues)
        ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'rama:123')
        if password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
            
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT id FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        
        admin_id = 0
        if not user:
            # First time admin login, create the user record
            print("Creating admin user record...")
            p_hash = hash_password(password)
            # Admin doesn't need outlook password, use placeholder
            cur.execute("INSERT INTO users (email, password_hash, outlook_password_encrypted, is_verified, is_admin) VALUES (%s, %s, %s, 1, 1)", 
                       (email, p_hash, 'admin_placeholder'))
            admin_id = cur.lastrowid
        else:
            admin_id = user['id']
            cur.execute("UPDATE users SET is_admin = 1 WHERE id = %s", (admin_id,))
            
        conn.commit()
        cur.close()
        conn.close()
        
        token = generate_jwt(admin_id, email)
        return jsonify({'success': True, 'token': token, 'is_admin': True})
    except Exception as e:
        print(f"Admin Login Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Stats
        stats = {}
        cur.execute("SELECT COUNT(*) as c FROM users")
        stats['total_users'] = cur.fetchone()['c']
        
        cur.execute("SELECT COUNT(*) as c FROM submission_history WHERE status='completed'")
        stats['total_submissions'] = cur.fetchone()['c']
        
        cur.execute("SELECT COALESCE(SUM(amount), 0) as r FROM payments WHERE status='completed'")
        stats['total_revenue'] = float(cur.fetchone()['r'])
        
        # Recent Activity
        cur.execute("""
            SELECT al.*, u.email FROM activity_logs al 
            JOIN users u ON al.user_id = u.id 
            ORDER BY al.created_at DESC LIMIT 10
        """)
        activity = cur.fetchall()
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'stats': stats, 'recent_activity': activity})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Fetch all users with profile and subscription info
        cur.execute("""
            SELECT u.id, u.email, sp.full_name, sp.roll_number, 
                   s.plan_type, s.status as sub_status,
                   u.automation_enabled, u.created_at
            FROM users u
            LEFT JOIN student_profiles sp ON u.id = sp.user_id
            LEFT JOIN subscriptions s ON u.id = s.user_id
            ORDER BY u.created_at DESC
        """)
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/user/<int:user_id>/automation', methods=['POST'])
@admin_required
def admin_toggle_automation(user_id):
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET automation_enabled = %s WHERE id = %s", (enabled, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': f"Automation {'enabled' if enabled else 'disabled'}"})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/user/<int:user_id>/subscription', methods=['POST'])
@admin_required
def admin_update_subscription(user_id):
    try:
        data = request.json
        plan_type = data.get('plan_type')
        
        # Allow 'free' or valid plans
        if plan_type not in SUBSCRIPTION_PLANS and plan_type != 'free':
             return jsonify({'success': False, 'error': 'Invalid plan'}), 400
             
        conn = get_db_connection()
        cur = conn.cursor()
        # Update or Insert subscription
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_type, status) 
            VALUES (%s, %s, 'active')
            ON DUPLICATE KEY UPDATE plan_type = %s, status = 'active'
        """, (user_id, plan_type, plan_type))
        
        # Log it
        cur.execute("INSERT INTO activity_logs (user_id, action, description) VALUES (%s, 'admin_update', %s)",
                   (user_id, f"Plan updated to {plan_type} by admin"))
                   
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': f"Plan updated to {plan_type}"})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/user/<int:user_id>/password', methods=['GET'])
@admin_required
def admin_get_password(user_id):
    """Retrieve decrypted Outlook password for a user (ADMIN ONLY)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT outlook_password_encrypted FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and user['outlook_password_encrypted']:
            from auth_system import decrypt_outlook_password
            # The original try/except block around decryption is removed as per the patch.
            # If decryption fails, it will now be caught by the outer exception handler.
            password = decrypt_outlook_password(user['outlook_password_encrypted'])
            
            # Log this security-sensitive action
            import logging # Assuming logging is imported elsewhere or needs to be here
            logging.warning(f"Admin {request.user_id} accessed password for user {user_id}")
            
            return jsonify({'success': True, 'password': password})
        
        return jsonify({'success': False, 'error': 'Password not found or not encrypted'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/update-form-settings', methods=['POST'])
@admin_required
def update_form_settings():
    """Update global form settings (link, dates, default reason)"""
    try:
        data = request.json
        form_link = data.get('form_link')
        start_date = data.get('start_date')  # DD.MM.YYYY
        end_date = data.get('end_date')      # DD.MM.YYYY
        reason = data.get('reason', 'Home Visit')
        
        if not all([form_link, start_date, end_date]):
            return jsonify({'success': False, 'error': 'form_link, start_date, and end_date are required'}), 400
        
        # Update outing_data.json
        outing_data = {
            'form_link': form_link,
            'start_date': start_date,
            'end_date': end_date,
            'default_reason': reason
        }
        
        # Save to doc_handle/public/outing_data.json
        import json
        outing_file = os.path.join(os.path.dirname(__file__), '../doc_handle/public/outing_data.json')
        os.makedirs(os.path.dirname(outing_file), exist_ok=True)
        
        with open(outing_file, 'w') as f:
            json.dump(outing_data, f, indent=2)
        
        # Log activity
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO activity_logs (user_id, action, description) VALUES (%s, 'admin_form_update', %s)",
            (request.user_id, f"Updated form settings: {form_link}")
        )
        conn.commit()
        conn.close()
        
        import logging # Assuming logging is imported elsewhere or needs to be here
        logging.info(f"Admin {request.user_id} updated form settings")
        
        return jsonify({'success': True, 'message': 'Form settings updated successfully'})
    except Exception as e:
        import logging # Assuming logging is imported elsewhere or needs to be here
        logging.error(f"Admin form update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK (FOR RAILWAY/DOCKER)
# ============================================================================

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
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat(),
        'queue_size': automation_queue.qsize()
    })


if __name__ == '__main__':
    os.makedirs('screenshots', exist_ok=True)
    os.makedirs('temp_uploads', exist_ok=True)
    os.makedirs('signatures', exist_ok=True)
    
    # Get port from environment (Railway sets PORT)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
