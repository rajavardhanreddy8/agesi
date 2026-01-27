-- Complete Database Schema for Outing Automation System
-- Run this to create all tables

-- Users Table (Main Authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,  -- College email (username)
    password_hash TEXT NOT NULL,         -- Hashed password (bcrypt)
    outlook_password_encrypted TEXT NOT NULL,  -- Encrypted Outlook password for automation
    
    -- Account Status
    is_verified BOOLEAN DEFAULT FALSE,   -- Email verification status
    is_active BOOLEAN DEFAULT TRUE,      -- Account active/suspended
    verification_token TEXT,             -- Email verification token
    verification_expires TIMESTAMP,
    
    -- Password Reset
    reset_token TEXT,
    reset_token_expires TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Student Profiles Table
CREATE TABLE IF NOT EXISTS student_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Personal Information
    full_name VARCHAR(255) NOT NULL,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Academic Details
    school VARCHAR(100) NOT NULL,  -- e.g., "School of Technology"
    academic_year VARCHAR(20) NOT NULL,  -- e.g., "2024-2028"
    programme VARCHAR(50) NOT NULL,  -- e.g., "B.Tech"
    specialization VARCHAR(100) NOT NULL,  -- e.g., "CSE"
    
    -- Contact Information
    student_phone VARCHAR(15) NOT NULL,
    student_email VARCHAR(255),  -- Personal email (optional)
    
    -- Parent/Guardian 1 Details
    parent1_name VARCHAR(255) NOT NULL,
    parent1_email VARCHAR(255) NOT NULL,
    parent1_phone VARCHAR(15) NOT NULL,
    parent1_relation VARCHAR(50) DEFAULT 'Father',  -- Father/Mother/Guardian
    
    -- Parent/Guardian 2 Details (Optional)
    parent2_name VARCHAR(255),
    parent2_email VARCHAR(255),
    parent2_phone VARCHAR(15),
    parent2_relation VARCHAR(50) DEFAULT 'Mother',
    
    -- Signature (Base64 encoded image)
    signature_data TEXT,  -- Stores signature image for PDF
    
    -- Preferences
    default_reason TEXT DEFAULT 'home',  -- Default reason for leave
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions Table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Subscription Details
    plan_type VARCHAR(50) DEFAULT 'free',  -- free, basic, premium
    is_auto_submit BOOLEAN DEFAULT FALSE,  -- Auto-submit forms weekly
    is_email_notifications BOOLEAN DEFAULT TRUE,
    is_sms_notifications BOOLEAN DEFAULT FALSE,
    
    -- Limits
    monthly_submissions_limit INTEGER DEFAULT 10,
    submissions_used INTEGER DEFAULT 0,
    
    -- Billing (if implementing paid plans)
    subscription_start DATE,
    subscription_end DATE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Submissions History Table
CREATE TABLE IF NOT EXISTS submission_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Submission Details
    form_url TEXT NOT NULL,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Dates
    leave_start_date DATE NOT NULL,
    leave_end_date DATE NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- pending, running, completed, failed
    progress INTEGER DEFAULT 0,
    message TEXT,
    error_details TEXT,
    
    -- Files
    pdf_path TEXT,
    screenshot_path TEXT,
    
    -- Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Metadata
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activity Details
    action VARCHAR(100) NOT NULL,  -- login, logout, profile_update, submission, etc.
    description TEXT,
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Verification Tokens Table
CREATE TABLE IF NOT EXISTS verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL,  -- email_verification, password_reset
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_student_profiles_roll_number ON student_profiles(roll_number);
CREATE INDEX idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX idx_submissions_user_id ON submission_history(user_id);
CREATE INDEX idx_submissions_status ON submission_history(status);
CREATE INDEX idx_submissions_date ON submission_history(leave_start_date);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_profiles_updated_at BEFORE UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample Data (for testing)
-- DO NOT use in production - these are examples only!

-- Example User (password is 'password123' hashed with bcrypt)
INSERT INTO users (email, password_hash, outlook_password_encrypted, is_verified) VALUES
('test@woxsen.edu.in', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7C3RKD4t0i', 'ENCRYPTED_PASSWORD_HERE', true)
ON CONFLICT (email) DO NOTHING;

-- Example Student Profile
INSERT INTO student_profiles (
    user_id, full_name, roll_number, school, academic_year, programme, specialization,
    student_phone, parent1_name, parent1_email, parent1_phone,
    parent2_name, parent2_email, parent2_phone
) VALUES (
    1, 'Test Student', '24WU0000000', 'School of Technology', '2024-2028', 'B.Tech', 'CSE',
    '0000000000', 'Test Father', 'father@test.com', '0000000000',
    'Test Mother', 'mother@test.com', '0000000000'
)
ON CONFLICT (user_id) DO NOTHING;

-- Example Subscription
INSERT INTO subscriptions (user_id, plan_type, is_auto_submit) VALUES
(1, 'free', false)
ON CONFLICT (user_id) DO NOTHING;

-- Views for Easy Data Access

-- Complete User Profile View
CREATE OR REPLACE VIEW v_user_profiles AS
SELECT 
    u.id as user_id,
    u.email,
    u.is_verified,
    u.is_active,
    u.last_login,
    sp.full_name,
    sp.roll_number,
    sp.school,
    sp.academic_year,
    sp.programme,
    sp.specialization,
    sp.student_phone,
    sp.parent1_name,
    sp.parent1_email,
    sp.parent1_phone,
    sp.parent2_name,
    sp.parent2_email,
    sp.parent2_phone,
    s.plan_type,
    s.is_auto_submit,
    s.monthly_submissions_limit,
    s.submissions_used
FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id;

-- Recent Submissions View
CREATE OR REPLACE VIEW v_recent_submissions AS
SELECT 
    sh.id,
    sh.user_id,
    sp.full_name,
    sp.roll_number,
    sh.leave_start_date,
    sh.leave_end_date,
    sh.status,
    sh.submitted_at,
    sh.completed_at
FROM submission_history sh
JOIN student_profiles sp ON sh.user_id = sp.user_id
ORDER BY sh.submitted_at DESC;

-- Database Statistics View
CREATE OR REPLACE VIEW v_database_stats AS
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE is_verified = true) as verified_users,
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM submission_history WHERE status = 'completed') as successful_submissions,
    (SELECT COUNT(*) FROM submission_history WHERE status = 'failed') as failed_submissions,
    (SELECT COUNT(*) FROM submission_history WHERE submitted_at > NOW() - INTERVAL '7 days') as submissions_last_7_days;
