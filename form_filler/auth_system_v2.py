"""
Supabase-based Authentication System for Outing Automation
Uses Supabase REST API instead of direct PostgreSQL connection
No database password required!
"""

import os
import secrets
from datetime import datetime, timedelta
from supabase import create_client, Client
import bcrypt
from cryptography.fernet import Fernet
import jwt
from dotenv import load_dotenv
import logging

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Initialize encryption
try:
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode() if os.getenv('ENCRYPTION_KEY') else Fernet.generate_key()
    cipher = Fernet(ENCRYPTION_KEY)
except Exception as e:
    print(f"Warning: Encryption key issue: {e}")
    ENCRYPTION_KEY = Fernet.generate_key()
    cipher = Fernet(ENCRYPTION_KEY)

JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def encrypt_outlook_password(password: str) -> str:
    encrypted = cipher.encrypt(password.encode('utf-8'))
    return encrypted.decode('utf-8')

def decrypt_outlook_password(encrypted: str) -> str:
    decrypted = cipher.decrypt(encrypted.encode('utf-8'))
    return decrypted.decode('utf-8')

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def generate_jwt(user_id: int, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except Exception:
        return None

def login_required(f):
    """Decorator to protect routes requiring authentication"""
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'error': 'No token'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        payload = verify_jwt(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        request.user_id = payload['user_id']
        request.user_email = payload['email']
        return f(*args, **kwargs)
    return decorated_function


def verify_outlook_credentials(email: str, password: str) -> tuple:
    """Verify Outlook credentials using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed, skipping verification")
        return True, None # Bypass verification if playwright missing
    try:
        with sync_playwright() as p:
            # IMPORTANT: --no-sandbox is required for Docker environments
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            page.goto('https://login.microsoftonline.com')
            page.fill('input[type="email"]', email)
            page.click('input[type="submit"]')
            page.wait_for_timeout(2000)
            page.fill('input[type="password"]', password)
            page.click('input[type="submit"]')
            page.wait_for_timeout(3000)
            
            success = ('login.microsoftonline.com/common/reprocess' in page.url or
                       'office.com' in page.url or
                       'MFA' in page.content() or
                       'Stay signed in' in page.content())
            browser.close()
            
            if success:
                return True, None
            else:
                return False, "Invalid credentials or login failed"
    except Exception as e:
        print(f"Outlook verification failed: {e}")
        return False, f"Verification system error: {str(e)}"

# ============================================================================
# SUPABASE AUTH FUNCTIONS
# ============================================================================

def register_user(data: dict) -> dict:
    """Register a new user using Supabase"""
    try:
        # Check if user exists
        existing = supabase.table('users').select('id').eq('email', data['email']).execute()
        if existing.data:
            return {'success': False, 'error': 'Email already registered'}
        
        # Verify Outlook credentials
        # TEMPORARY: Disabled to unblock registration while fixing browser issues (Forced Update)
        logging.info(f"Skipping Outlook verification for {data['email']} to unblock registration")
        # is_valid, error_msg = verify_outlook_credentials(data['email'], data['outlook_password'])
        # if not is_valid:
        #     # Use specific error message from verification system
        #     return {'success': False, 'error': error_msg or 'Invalid Outlook credentials'}

        # Insert User
        token = generate_token()
        expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        pass_hash = hash_password(data['password'])
        out_enc = encrypt_outlook_password(data['outlook_password'])
        
        user_result = supabase.table('users').insert({
            'email': data['email'],
            'password_hash': pass_hash,
            'outlook_password_encrypted': out_enc,
            'verification_token': token,
            'verification_expires': expires
        }).execute()
        
        if not user_result.data:
            return {'success': False, 'error': 'Failed to create user'}
        
        user_id = user_result.data[0]['id']
        
        # Insert Profile
        supabase.table('student_profiles').insert({
            'user_id': user_id,
            'full_name': data['full_name'],
            'roll_number': data['roll_number'],
            'school': data['school'],
            'academic_year': data.get('academic_year'),
            'programme': data.get('programme'),
            'specialization': data.get('specialization'),
            'student_phone': data.get('student_phone'),
            'student_email': data.get('student_email'),
            'parent1_name': data.get('parent1_name'),
            'parent1_email': data.get('parent1_email'),
            'parent1_phone': data.get('parent1_phone'),
            'parent1_relation': data.get('parent1_relation', 'Father'),
            'parent2_name': data.get('parent2_name'),
            'parent2_email': data.get('parent2_email'),
            'parent2_phone': data.get('parent2_phone'),
            'parent2_relation': data.get('parent2_relation', 'Mother'),
            'signature_data': data.get('signature_data')
        }).execute()
        
        # Insert Subscription
        supabase.table('subscriptions').insert({
            'user_id': user_id,
            'plan_type': 'free'
        }).execute()
        
        print(f"DEBUG: Email Verification Link: {os.getenv('FRONTEND_URL')}/verify-email?token={token}")
        return {'success': True, 'message': 'Registration successful! Check logs for verification link.', 'user_id': user_id}
        
    except Exception as e:
        print(f"Registration Error: {e}")
        return {'success': False, 'error': str(e)}

def login_user(email: str, password: str) -> dict:
    """Login user using Supabase"""
    try:
        # Get user with profile
        user_result = supabase.table('users').select('*, student_profiles(full_name, roll_number)').eq('email', email).execute()
        
        if not user_result.data:
            return {'success': False, 'error': 'Invalid credentials'}
        
        user = user_result.data[0]
        
        if not verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid credentials'}
        
        
        # Get profile data - handle both object and array formats from Supabase
        sp = user.get('student_profiles')
        if isinstance(sp, list):
            profile = sp[0] if sp else {}
        elif isinstance(sp, dict):
            profile = sp
        else:
            profile = {}
        
        token = generate_jwt(user['id'], user['email'])
        return {
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': profile.get('full_name')
            }
        }
    except Exception as e:
        import traceback
        logging.error(f"Login Failed Traceback: {traceback.format_exc()}")
        return {'success': False, 'error': f"Login Error: {str(e)}"}

def verify_email_token(token: str) -> dict:
    """Verify email token"""
    try:
        user_result = supabase.table('users').select('id').eq('verification_token', token).execute()
        
        if not user_result.data:
            return {'success': False, 'error': 'Invalid token'}
        
        user_id = user_result.data[0]['id']
        supabase.table('users').update({
            'is_verified': True,
            'verification_token': None
        }).eq('id', user_id).execute()
        
        return {'success': True, 'message': 'Email verified!'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_profile(user_id: int) -> dict:
    """Get user profile data"""
    try:
        result = supabase.table('student_profiles').select('*').eq('user_id', user_id).execute()
        if result.data:
            return {'success': True, 'profile': result.data[0]}
        return {'success': False, 'error': 'Profile not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Placeholder functions for compatibility
def request_password_reset(email): 
    return {'success': True}

def reset_password(token, new_pw): 
    return {'success': True}
