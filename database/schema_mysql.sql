-- Complete Database Schema for Outing Automation System (MySQL)

-- Users Table (Main Authentication)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    outlook_password_encrypted TEXT NOT NULL,
    
    -- Account Status
    is_verified TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    is_admin TINYINT(1) DEFAULT 0,
    verification_token TEXT,
    verification_expires DATETIME,
    
    -- Password Reset
    reset_token TEXT,
    reset_token_expires DATETIME,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- Student Profiles Table
CREATE TABLE IF NOT EXISTS student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    CONSTRAINT fk_sp_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Personal Information
    full_name VARCHAR(255) NOT NULL,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Academic Details
    school VARCHAR(100) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    programme VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    
    -- Contact Information
    student_phone VARCHAR(15) NOT NULL,
    student_email VARCHAR(255),
    
    -- Parent/Guardian 1 Details
    parent1_name VARCHAR(255) NOT NULL,
    parent1_email VARCHAR(255) NOT NULL,
    parent1_phone VARCHAR(15) NOT NULL,
    parent1_relation VARCHAR(50) DEFAULT 'Father',
    
    -- Parent/Guardian 2 Details (Optional)
    parent2_name VARCHAR(255),
    parent2_email VARCHAR(255),
    parent2_phone VARCHAR(15),
    parent2_relation VARCHAR(50) DEFAULT 'Mother',
    
    -- Signature
    signature_data MEDIUMTEXT,
    
    -- Preferences
    default_reason TEXT,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    CONSTRAINT fk_sub_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    plan_type VARCHAR(50) DEFAULT 'free',
    is_auto_submit TINYINT(1) DEFAULT 0,
    is_email_notifications TINYINT(1) DEFAULT 1,
    is_sms_notifications TINYINT(1) DEFAULT 0,
    
    monthly_submissions_limit INT DEFAULT 10,
    submissions_used INT DEFAULT 0,
    
    subscription_start DATE,
    subscription_end DATE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    CONSTRAINT fk_pay_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    plan_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    
    payment_gateway VARCHAR(50) DEFAULT 'razorpay',
    payment_order_id VARCHAR(255),
    payment_id VARCHAR(255),
    
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed, refunded
    
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Submissions History Table
CREATE TABLE IF NOT EXISTS submission_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    CONSTRAINT fk_hist_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    form_url TEXT NOT NULL,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    
    leave_start_date DATE NOT NULL,
    leave_end_date DATE NOT NULL,
    
    status VARCHAR(20) NOT NULL,
    progress INT DEFAULT 0,
    message TEXT,
    error_details TEXT,
    
    pdf_path TEXT,
    screenshot_path TEXT,
    
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    CONSTRAINT fk_act_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    action VARCHAR(100) NOT NULL,
    description TEXT,
    
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Verification Tokens Table
CREATE TABLE IF NOT EXISTS verification_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    CONSTRAINT fk_vt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    token TEXT NOT NULL,
    token_type VARCHAR(20) NOT NULL,
    expires_at DATETIME NOT NULL,
    used TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_student_profiles_roll_number ON student_profiles(roll_number);
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_submissions_user_id ON submission_history(user_id);
CREATE INDEX idx_submissions_status ON submission_history(status);
CREATE INDEX idx_submissions_date ON submission_history(leave_start_date);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);

-- Views
CREATE OR REPLACE VIEW v_user_profiles AS
SELECT 
    u.id as user_id, u.email, u.is_verified, u.is_active, u.is_admin, u.last_login,
    sp.full_name, sp.roll_number, sp.school, sp.academic_year, sp.programme, sp.specialization,
    sp.student_phone, sp.parent1_name, sp.parent1_email, sp.parent1_phone,
    sp.parent2_name, sp.parent2_email, sp.parent2_phone,
    s.plan_type, s.is_auto_submit, s.monthly_submissions_limit, s.submissions_used
FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id;

CREATE OR REPLACE VIEW v_recent_submissions AS
SELECT 
    sh.id, sh.user_id, sp.full_name, sp.roll_number,
    sh.leave_start_date, sh.leave_end_date, sh.status,
    sh.submitted_at, sh.completed_at
FROM submission_history sh
JOIN student_profiles sp ON sh.user_id = sp.user_id
ORDER BY sh.submitted_at DESC;

CREATE OR REPLACE VIEW v_database_stats AS
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE is_verified = 1) as verified_users,
    (SELECT COUNT(*) FROM users WHERE is_active = 1) as active_users,
    (SELECT COUNT(*) FROM submission_history WHERE status = 'completed') as successful_submissions,
    (SELECT COUNT(*) FROM submission_history WHERE status = 'failed') as failed_submissions,
    (SELECT COUNT(*) FROM submission_history WHERE submitted_at > NOW() - INTERVAL 7 DAY) as submissions_last_7_days;
