-- Complete Database Schema for Outing Automation System (PostgreSQL/Supabase)
-- CLEAN RESET VERSION - This will delete everything and start fresh!

-- Drop existing views first (dependencies)
DROP VIEW IF EXISTS v_database_stats;
DROP VIEW IF EXISTS v_recent_submissions;
DROP VIEW IF EXISTS v_user_profiles;

-- Force Drop existing tables to ensure absolute synchronization
DROP TABLE IF EXISTS verification_tokens;
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS submission_history;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS student_profiles;
DROP TABLE IF EXISTS users;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    outlook_password_encrypted TEXT NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    verification_token TEXT,
    verification_expires TIMESTAMP,
    reset_token TEXT,
    reset_token_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Trigger for users
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Student Profiles Table
CREATE TABLE student_profiles (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    school VARCHAR(100) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    programme VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    student_phone VARCHAR(15) NOT NULL,
    student_email VARCHAR(255),
    parent1_name VARCHAR(255) NOT NULL,
    parent1_email VARCHAR(255) NOT NULL,
    parent1_phone VARCHAR(15) NOT NULL,
    parent1_relation VARCHAR(50) DEFAULT 'Father',
    parent2_name VARCHAR(255),
    parent2_email VARCHAR(255),
    parent2_phone VARCHAR(15),
    parent2_relation VARCHAR(50) DEFAULT 'Mother',
    signature_data TEXT,
    default_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger for student_profiles
CREATE TRIGGER update_student_profiles_updated_at BEFORE UPDATE ON student_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Subscriptions Table
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) DEFAULT 'free',
    is_auto_submit BOOLEAN DEFAULT FALSE,
    is_email_notifications BOOLEAN DEFAULT TRUE,
    is_sms_notifications BOOLEAN DEFAULT FALSE,
    monthly_submissions_limit INT DEFAULT 10,
    submissions_used INT DEFAULT 0,
    subscription_start DATE,
    subscription_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger for subscriptions
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Payments Table (MySQL Amount changed to Decimal for Postgres compatibility)
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    payment_gateway VARCHAR(50) DEFAULT 'razorpay',
    payment_order_id VARCHAR(255),
    payment_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Submission History Table
CREATE TABLE submission_history (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
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
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Activity Logs Table
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verification Tokens Table
CREATE TABLE verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    token_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_student_profiles_roll_number ON student_profiles(roll_number);
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_submissions_user_id ON submission_history(user_id);
CREATE INDEX idx_submissions_status ON submission_history(status);

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
    (SELECT COUNT(*) FROM users WHERE is_verified = TRUE) as verified_users,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
    (SELECT COUNT(*) FROM submission_history WHERE status = 'completed') as successful_submissions,
    (SELECT COUNT(*) FROM submission_history WHERE status = 'failed') as failed_submissions,
    (SELECT COUNT(*) FROM submission_history WHERE submitted_at > NOW() - INTERVAL '7 days') as submissions_last_7_days;
