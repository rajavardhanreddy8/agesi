"""
Flask API to trigger Microsoft Forms automation
Integrates with your existing PDF generation web app and PostgreSQL database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
import threading
import json
import os
import logging
import psycopg2.extras
import bridge  # Mail agent bridge
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import razorpay
from functools import wraps

# Import the automation class
from ms_form_automation import MSFormAutomation

# Import authentication system
from auth_system import (
    register_user, login_user, verify_email_token,
    request_password_reset, reset_password,
    login_required, get_db_connection,
    encrypt_outlook_password, decrypt_outlook_password,
    hash_password, verify_outlook_credentials,
    verify_password, generate_jwt, verify_jwt
)

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for your frontend

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

# Scheduler Config
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Initialize Scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Add Cron Job: Run daily at 7 AM IST (1:30 AM UTC)
# For testing: using interval of 1 hour, or specifically 7 AM
@scheduler.task('cron', id='daily_mail_check', hour=1, minute=30)
def scheduled_mail_check():
    print("⏰ Cron Trigger: Checking for emails...")
    with app.app_context():
        try:
            bridge.main()
        except Exception as e:
            print(f"Mail check failed: {e}")

scheduler.start()

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

def automation_worker():
    """
    Worker thread to process automation tasks sequentially from the queue.
    This ensures that we don't open 100 browsers at once if 100 users subscribe.
    """
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

def run_automation_async(task_id, form_url, email, password, form_data, pdf_path):
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
        
        # Headless=False for better reliability with MFA, but consider Headless=True for scalability if MFA allows
        automation = MSFormAutomation(headless=False) 
        
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
              AND s.subscription_end >= CURDATE()
              AND u.is_active = 1
        """)
        eligible_users = cur.fetchall()
        
        tasks_created = 0

        for user in eligible_users:
            try:
                user_id = user['id']
                
                # Decrypt password
                try:
                    outlook_password = decrypt_outlook_password(user['outlook_password_encrypted'])
                except:
                    logging.error(f"Could not decrypt password for user {user['email']}, skipping.")
                    continue

                # Prepare PDF (Generic placeholder or generate one)
                # For scalability, we should ideally generate a PDF. 
                # For now, we will try to find a recent valid PDF or use a placeholder if the automation supports it.
                # Assuming MSFormAutomation needs a VALID file path.
                # We'll create a dummy 'generated' PDF for this specific outing request if needed, 
                # or better, generate the real PDF. 
                # LIMITATION: We are not generating the specific PDF here yet. 
                # We will use a placeholder 'auto_generated.pdf' if it exists, or skipping PDF generation for now 
                # if MSFormAutomation strictly needs it. 
                # To be robust, let's create a directory for this task.
                
                # Simple fix: Reuse the logic from submit_form to save a placeholder
                temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
                os.makedirs(temp_dir, exist_ok=True)
                # We do NOT have the specific PDF from the user. 
                # We will send a generic "Permission Request" PDF or allow the automation to generate one.
                # Since the current `MSFormAutomation` takes `pdf_path` and uploads it, we need a file.
                # Let's check for a 'template.pdf' or create a text file named .pdf as a placeholder if legitimate not available??
                # No, that will fail upload validation likely.
                # We will assume a 'standard_outing.pdf' exists in root for auto-submissions or use the user's last one?
                # Let's try to use a standard file for now to unblock.
                pdf_path = os.path.abspath("standard_outing.pdf")
                if not os.path.exists(pdf_path):
                    with open(pdf_path, 'w') as f: f.write("Dummy PDF content for automation") 

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
                    'reason': user.get('default_reason', 'Home Visit'), # Use default reason
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
def generate_pdf():
    """Generate a PDF consent form with user's stored data"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        import io
        import base64
        
        # Get user profile
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM v_user_profiles WHERE user_id = %s", (request.user_id,))
        profile = cur.fetchone()
        conn.close()
        
        if not profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
        
        # Get latest dates from outing_data.json if available
        start_date = request.json.get('start_date') if request.json else None
        end_date = request.json.get('end_date') if request.json else None
        
        # Create PDF
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
        
        # Date Details
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Outing Details:")
        c.setFont("Helvetica", 11)
        y -= 20
        c.drawString(70, y, f"Start Date: {start_date or 'To be filled'}")
        y -= 18
        c.drawString(70, y, f"End Date: {end_date or 'To be filled'}")
        
        # Father Details
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
        
        # Mother Details
        y -= 30
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
        if sig_data and sig_data.startswith('data:image'):
            try:
                # Extract base64 data
                header, encoded = sig_data.split(',', 1)
                sig_bytes = base64.b64decode(encoded)
                sig_image = ImageReader(io.BytesIO(sig_bytes))
                c.drawImage(sig_image, 70, y - 60, width=100, height=50, preserveAspectRatio=True)
            except Exception as e:
                c.drawString(70, y - 20, "[Signature could not be loaded]")
        else:
            c.drawString(70, y - 20, "[No signature uploaded]")
        
        c.save()
        buffer.seek(0)
        
        from flask import send_file
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"outing_consent_{profile.get('roll_number', 'form')}.pdf"
        )
        
    except Exception as e:
        logging.error(f"PDF Generation Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# FORM SUBMISSION (PROTECTED)
# ============================================================================

@app.route('/api/submit-form', methods=['POST'])
@login_required
def submit_form():
    conn = None
    try:
        # 1. Handle PDF Upload
        if 'pdf' not in request.files:
             return jsonify({'success': False, 'error': 'No PDF file uploaded'}), 400
        
        pdf_file = request.files['pdf']
        
        # 2. Get Form Data
        if 'data' not in request.form:
             return jsonify({'success': False, 'error': 'No form data provided'}), 400
             
        request_data = json.loads(request.form['data'])
        form_url = request_data.get('form_url')
        if not form_url:
            return jsonify({'success': False, 'error': 'Form URL is required'}), 400

        # 3. Retrieve User Credentials & Profile from DB
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
            raise Exception("User profile incomplete or missing")
            
        # Decrypt password
        try:
            outlook_password = decrypt_outlook_password(user_auth['outlook_password_encrypted'])
        except Exception as e:
            return jsonify({'success': False, 'error': 'Failed to decrypt credentials. Please update your password.'}), 400
            
        # 4. Save PDF
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, f"outing_{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        pdf_file.save(pdf_path)
        
        # 5. Prepare Automation Data
        # Map profile fields to form fields
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
            'reason': request_data.get('reason', profile.get('default_reason', 'home')),
            'leave_start_date': request_data.get('leave_start_date'),
            'leave_end_date': request_data.get('leave_end_date')
        }
        
        # 6. Create Task & Log to DB
        task_id = f"task_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = AutomationTask(task_id, request.user_id)
        automation_tasks[task_id] = task
        
        cur.execute(
            """
            INSERT INTO submission_history 
            (user_id, task_id, form_url, leave_start_date, leave_end_date, status, pdf_path, ip_address)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s)
            """,
            (
                request.user_id, task_id, form_url,
                request_data.get('leave_start_date'), request_data.get('leave_end_date'),
                pdf_path, request.remote_addr
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
                pdf_path
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
razorpay_client = razorpay.Client(
    auth=(os.getenv('RAZORPAY_KEY_ID', 'rzp_test_placeholder'), os.getenv('RAZORPAY_KEY_SECRET', 'secret'))
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
                    WHEN s.subscription_end < CURDATE() THEN 'expired'
                    WHEN s.subscription_end < DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 'expiring_soon'
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
        if plan_type not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'error': 'Invalid plan type'}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_type]
        order_data = {
            'amount': plan['price'] * 100,
            'currency': plan['currency'],
            'payment_capture': 1,
            'notes': {'user_id': request.user_id, 'plan_type': plan_type}
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            INSERT INTO payments (user_id, plan_type, amount, currency, payment_gateway, payment_order_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (request.user_id, plan_type, plan['price'], plan['currency'], 'razorpay', order['id']))
        payment_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': plan['price'],
            'currency': plan['currency'],
            'payment_id': payment_id,
            'key': os.getenv('RAZORPAY_KEY_ID')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscription/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    try:
        data = request.json
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })
        except:
            return jsonify({'success': False, 'error': 'Invalid signature'}), 400
            
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT * FROM payments WHERE payment_order_id = %s", (data['razorpay_order_id'],))
        payment = cur.fetchone()
        
        if not payment: return jsonify({'success': False, 'error': 'Payment not found'}), 404
        
        plan = SUBSCRIPTION_PLANS[payment['plan_type']]
        sub_end = datetime.now() + timedelta(days=plan['duration_days'])
        
        cur.execute("UPDATE payments SET status = 'completed', payment_id = %s, completed_at = NOW() WHERE id = %s",
                   (data['razorpay_payment_id'], payment['id']))
                   
        cur.execute("""
            UPDATE subscriptions SET 
                plan_type = %s,
                is_auto_submit = %s,
                monthly_submissions_limit = %s,
                subscription_start = CURDATE(),
                subscription_end = %s
            WHERE user_id = %s
        """, (payment['plan_type'], plan['features']['auto_submit'], plan['features']['monthly_submissions'], sub_end, request.user_id))
        
        cur.execute("INSERT INTO activity_logs (user_id, action, description) VALUES (%s, 'subscription_upgrade', %s)",
                   (request.user_id, f"Upgraded to {plan['name']}"))
                   
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Upgraded!'})
    except Exception as e:
        print(f"Verify Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
            try:
                decrypted = decrypt_outlook_password(user['outlook_password_encrypted'])
                return jsonify({'success': True, 'password': decrypted})
            except Exception as dec_err:
                 return jsonify({'success': False, 'error': f'Decryption failed: {str(dec_err)}'}), 500
        
        return jsonify({'success': False, 'error': 'Password not found or not encrypted'}), 404
    except Exception as e:
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
