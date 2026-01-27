
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
        'price': 99,
        'currency': 'INR',
        'duration_days': 120,
        'features': {
            'monthly_submissions': 20,
            'auto_submit': True,
            'email_notifications': True,
            'sms_notifications': False,
            'priority_support': False,
            'data_backup': True
        }
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 199,
        'currency': 'INR',
        'duration_days': 120,
        'features': {
            'monthly_submissions': 999,
            'auto_submit': True,
            'email_notifications': True,
            'sms_notifications': True,
            'priority_support': True,
            'data_backup': True,
            'early_access': True
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
        cur = conn.cursor(dictionary=True)
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
        cur = conn.cursor(dictionary=True)
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
        cur = conn.cursor(dictionary=True)
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
        cur = conn.cursor(dictionary=True)
        
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
            
        if not verify_password(password, ADMIN_PASSWORD_HASH):
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
            
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        
        admin_id = 0
        if not user:
            # First time admin login, create the user record
            print("Creating admin user record...")
            p_hash = hash_password(password) # Use the input password (or admin hash?) - actually we should store the hash in DB
            # But here we verify against ENV. So we just need a user record for FKs.
            # We'll insert with the hash we have.
            cur.execute("INSERT INTO users (email, password_hash, is_verified, is_admin) VALUES (%s, %s, 1, 1)", 
                       (email, ADMIN_PASSWORD_HASH))
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
        cur = conn.cursor(dictionary=True)
        
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
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.id, u.email, sp.full_name, sp.roll_number, s.plan_type, u.is_active 
        FROM users u 
        LEFT JOIN student_profiles sp ON u.id = sp.user_id 
        LEFT JOIN subscriptions s ON u.id = s.user_id
        ORDER BY u.created_at DESC
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({'success': True, 'users': users})
