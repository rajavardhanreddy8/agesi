
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, BookOpen, Users, PenTool, Download, LogOut, Calendar, Edit3, Send, Loader, CheckCircle, AlertCircle, Zap } from 'lucide-react';
import { auth } from '../utils/auth';
import api from '../utils/api';
import { generateOutingPDF } from '../utils/pdfGenerator';

const Dashboard = () => {
    const navigate = useNavigate();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [outingData, setOutingData] = useState({
        startDate: '',
        endDate: '',
        formLink: ''
    });
    const [submission, setSubmission] = useState({
        loading: false,
        taskId: null,
        status: null, // 'pending', 'running', 'completed', 'failed'
        message: '',
        progress: 0,
        queuePosition: null
    });
    const [reverifyModal, setReverifyModal] = useState({
        show: false,
        loading: false,
        password: '',
        error: ''
    });
    const [autoMode, setAutoMode] = useState({
        enabled: false,
        loading: false,
        planType: null,
    });

    // Helper to get pure base URL (no /api suffix)
    const getBaseUrl = () => {
        const url = import.meta.env.VITE_API_URL || 'https://outing-backend-api.azurewebsites.net/api';
        return url.replace(/\/api$/, '');
    };

    useEffect(() => {
        fetchProfile();
        fetchOutingData();
    }, []);

    const fetchProfile = async () => {
        try {
            const res = await api.get('/profile');
            if (res.data.success) {
                const userProfile = res.data.profile;
                setProfile(userProfile);

                // PAYWALL ENFORCEMENT
                // Check if user has an active basic or premium plan
                // We can check this via a separate API call or if profile includes sub info
                // Let's call the subscription/current endpoint to be sure
                try {
                    const subRes = await api.get('/subscription/current');
                    if (subRes.data.success) {
                        const plan = subRes.data.subscription;

                        // Check if the user is on the basic trial and has used up all their submissions
                        const isTrialExhausted = plan?.plan_type === 'basic' &&
                            plan?.submissions_used >= plan?.monthly_submissions_limit;

                        if (!plan || plan.plan_type === 'free' || plan.subscription_status === 'expired' || isTrialExhausted) {
                            // No valid plan or exhausted trial, redirect to payment
                            console.log("No active plan or trial exhausted, redirecting to plans...");
                            navigate('/plans');
                            return;
                        }

                        // Populate auto-mode state from subscription data
                        setAutoMode(prev => ({
                            ...prev,
                            enabled: !!plan?.is_auto_submit,
                            planType: plan?.plan_type,
                        }));
                    } else {
                        navigate('/plans');
                        return;
                    }
                } catch (subErr) {
                    console.error("Failed to verify subscription:", subErr);
                    navigate('/plans');
                    return;
                }
            }
        } catch (error) {
            console.error(error);
            if (error.response?.status === 401) navigate('/login');
        } finally {
            setLoading(false);
        }
    };

    const fetchOutingData = async () => {
        try {
            // Fetch latest config from backend API (source of truth)
            const res = await api.get('/config/active-outing');
            if (res.data.success) {
                const data = res.data;
                setOutingData({
                    startDate: data.start_date || new Date().toISOString().split('T')[0],
                    endDate: data.end_date || new Date(Date.now() + 172800000).toISOString().split('T')[0],
                    formLink: data.form_link || '',
                    reason: data.default_reason || ''
                });
            }
        } catch (e) {
            console.error("Failed to fetch outing config:", e);
            // Fallback to defaults
            setOutingData(prev => ({
                ...prev,
                startDate: new Date().toISOString().split('T')[0],
                endDate: new Date(Date.now() + 172800000).toISOString().split('T')[0]
            }));
        }
    };

    const handleDateChange = (e) => {
        setOutingData({ ...outingData, [e.target.name]: e.target.value });
    };

    const handleGeneratePdf = () => {
        if (!profile) return;
        generateOutingPDF({
            studentName: profile.full_name,
            studentId: profile.roll_number,
            program: profile.programme,
            academicYear: profile.academic_year?.split('-')[0],
            startDate: outingData.startDate,
            startTime: '17:30',
            endDate: outingData.endDate,
            endTime: '08:30',
            purpose: 'Outing',
            todayDate: new Date().toISOString().split('T')[0],
            fatherName: profile.parent1_name,
            fatherEmail: profile.parent1_email,
            fatherMobile: profile.parent1_phone,
            motherName: profile.parent2_name,
            motherEmail: profile.parent2_email,
            motherMobile: profile.parent2_phone,
            studentEmail: profile.email,
            studentMobile: profile.student_phone,
            signatureImage: (profile.signature_data?.startsWith('signatures/') || profile.signature_data?.startsWith('signatures\\')) ?
                `${getBaseUrl()}/${profile.signature_data.replace(/\\/g, '/')}` :
                profile.signature_data
        });
    };

    // Submit form via backend automation
    const handleSubmitForm = async () => {
        if (!profile) return;
        if (!outingData.formLink) {
            alert('Please enter the Microsoft Form link');
            return;
        }

        // STRICT VALIDATION: Check Profile Completeness
        const missingFields = [];
        if (!profile?.full_name) missingFields.push('Full Name');
        if (!profile?.roll_number) missingFields.push('Roll Number');
        if (!profile?.student_phone) missingFields.push('Student Phone');
        if (!profile?.student_email && !profile?.email) missingFields.push('Student Email');
        if (!profile?.parent1_name) missingFields.push('Parent 1 Name');
        if (!profile?.parent1_phone) missingFields.push('Parent 1 Phone');
        if (!profile?.parent1_email) missingFields.push('Parent 1 Email');

        if (missingFields.length > 0) {
            alert(`⚠️ INCOMPLETE PROFILE!\n\nThe following details are missing:\n- ${missingFields.join('\n- ')}\n\nPlease go to "Edit Profile" and fill these details before submitting.`);
            return;
        }

        if (!outingData.reason) {
            alert("⚠️ REASON REQUIRED!\n\nPlease enter a reason for the outing (e.g., 'Home Visit').");
            return;
        }

        setSubmission({ loading: true, taskId: null, status: 'starting', message: 'Initiating submission...', progress: 0 });

        try {
            // Send JSON payload with form URL, dates, and reason
            const payload = {
                form_url: outingData.formLink,
                leave_start_date: outingData.startDate,  // YYYY-MM-DD format
                leave_end_date: outingData.endDate,      // YYYY-MM-DD format
                reason: outingData.reason
            };

            const res = await api.post('/submit-form', payload);

            if (res.data.success && res.data.task_id) {
                setSubmission({
                    loading: false,
                    taskId: null,
                    status: 'completed',
                    message: '✅ Form queued successfully!',
                    progress: 100,
                    queuePosition: 0
                });

                alert("Your application has been queued. You will receive a confirmation mail after completion.");
            } else {
                setSubmission({ loading: false, taskId: null, status: 'failed', message: res.data.error || 'Failed to start', progress: 0 });
            }
        } catch (error) {
            console.error('Submit error:', error);

            // Check if it's a credential reverify error
            if (error.response?.data?.error_code === 'CREDENTIAL_REVERIFY_NEEDED') {
                setSubmission({ loading: false, taskId: null, status: null, message: '', progress: 0 });
                setReverifyModal({ show: true, loading: false, password: '', error: '' });
                return;
            }

            setSubmission({
                loading: false,
                taskId: null,
                status: 'failed',
                message: error.response?.data?.error || 'Connection failed',
                progress: 0
            });
        }
    };

    // Handle credential reverification
    const handleReverifyCredentials = async () => {
        if (!reverifyModal.password) {
            setReverifyModal(prev => ({ ...prev, error: 'Please enter your Outlook password' }));
            return;
        }

        setReverifyModal(prev => ({ ...prev, loading: true, error: '' }));

        try {
            const res = await api.post('/auth/reverify-credentials', {
                outlook_password: reverifyModal.password
            });

            if (res.data.success) {
                // Success! Close modal and retry submission
                setReverifyModal({ show: false, loading: false, password: '', error: '' });

                // Retry the form submission
                handleSubmitForm();
            } else {
                setReverifyModal(prev => ({ ...prev, loading: false, error: res.data.error || 'Verification failed' }));
            }
        } catch (error) {
            console.error('Reverify error:', error);
            setReverifyModal(prev => ({
                ...prev,
                loading: false,
                error: error.response?.data?.error || 'Verification failed. Please check your password.'
            }));
        }
    };

    // Toggle auto-submit mode for paid users
    const handleToggleAutoMode = async () => {
        const newVal = !autoMode.enabled;
        setAutoMode(prev => ({ ...prev, loading: true }));
        try {
            const res = await api.put('/subscription/auto-submit', { enabled: newVal });
            if (res.data.success) {
                setAutoMode(prev => ({ ...prev, enabled: newVal, loading: false }));
            } else {
                alert(res.data.error || 'Failed to update auto-submit');
                setAutoMode(prev => ({ ...prev, loading: false }));
            }
        } catch (e) {
            alert(e.response?.data?.error || 'Failed to update auto-submit');
            setAutoMode(prev => ({ ...prev, loading: false }));
        }
    };

    const theme = {
        bg: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        card: 'rgba(30, 41, 59, 0.7)',
        cardBorder: '1px solid rgba(255,255,255,0.08)',
        text: '#f8fafc',
        textMuted: '#94a3b8',
        primary: 'linear-gradient(135deg, #6366f1, #4f46e5)',
        accent: 'linear-gradient(135deg, #a855f7, #9333ea)',
    };

    if (loading) return <div className="dashboard-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>;

    const DetailRow = ({ label, value }) => (
        <div className="dash-row">
            <span className="dash-row-label">{label}</span>
            <span className="dash-row-val">{value || 'N/A'}</span>
        </div>
    );

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div className="dashboard-logo">campusouting</div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ color: theme.textMuted, fontSize: '0.9rem' }}>Welcome, {profile?.full_name?.split(' ')[0]}</span>
                    <button onClick={() => { auth.logout(); navigate('/login'); }} style={{ background: 'none', border: 'none', color: theme.textMuted, cursor: 'pointer' }}>
                        <LogOut size={20} />
                    </button>
                </div>
            </header>

            <main className="dashboard-main">
                <div className="dashboard-hero">
                    <div className="dashboard-avatar">{profile?.full_name?.charAt(0)}</div>
                    <div className="dashboard-hero-content">
                        <h1 className="dashboard-title">{profile?.full_name}</h1>
                        <div className="dashboard-badges">
                            <span className="dashboard-badge">{profile?.roll_number}</span>
                            <span className="dashboard-badge">{profile?.programme}</span>
                            <span className="dashboard-badge">{profile?.email}</span>
                        </div>
                        <div className="dashboard-btn-group">
                            <button onClick={() => navigate('/profile')} className="btn-dash btn-dash-secondary"><Edit3 size={18} /> Edit Profile</button>
                            {profile?.is_admin && (
                                <button onClick={() => window.location.href = '/admin/dashboard'} className="btn-dash btn-dash-secondary" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#f87171' }}>🛡️ Admin Portal</button>
                            )}
                            <button onClick={() => navigate('/plans')} className="btn-dash btn-dash-secondary" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24' }}>Upgrage Plan</button>
                        </div>
                    </div>

                    {/* Weekly Auto-Submit Toggle — visible to all paying users */}
                    {autoMode.planType && autoMode.planType !== 'free' && (
                        <div className="dashboard-gen-card" style={{
                            background: autoMode.enabled ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))' : 'rgba(30,41,59,0.7)',
                            border: autoMode.enabled ? '1px solid rgba(168, 85, 247, 0.5)' : '1px solid rgba(255,255,255,0.08)',
                            marginBottom: '1.5rem',
                            position: 'relative',
                            overflow: 'hidden',
                            transition: 'all 0.3s'
                        }}>
                            <div style={{ position: 'absolute', top: 0, right: 0, padding: '4px 12px', background: 'linear-gradient(135deg, #6366f1, #a855f7)', color: 'white', fontSize: '0.7rem', fontWeight: 'bold', borderBottomLeftRadius: '12px' }}>
                                PREMIUM FEATURE
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '0.2rem' }}>
                                    <div style={{ background: autoMode.enabled ? 'linear-gradient(135deg,#6366f1,#a855f7)' : 'rgba(255,255,255,0.06)', padding: '10px', borderRadius: '12px', transition: 'background 0.3s' }}>
                                        <Zap size={24} color={autoMode.enabled ? '#fff' : '#94a3b8'} />
                                    </div>
                                    <div>
                                        <h3 style={{ margin: 0, color: 'white', fontSize: '1.1rem', fontWeight: 'bold' }}>Weekly Auto-Submit</h3>
                                        <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.85rem' }}>
                                            {autoMode.enabled ? '🟢 Active — zero clicks needed every week.' : 'Enable to apply automatically for every outing.'}
                                        </p>
                                    </div>
                                </div>

                                {/* Toggle Switch */}
                                <button
                                    id="auto-submit-toggle"
                                    onClick={handleToggleAutoMode}
                                    disabled={autoMode.loading}
                                    style={{
                                        width: 56, height: 30, borderRadius: 15, border: 'none', cursor: autoMode.loading ? 'wait' : 'pointer',
                                        background: autoMode.enabled ? '#a855f7' : 'rgba(255,255,255,0.1)',
                                        position: 'relative', flexShrink: 0, transition: 'background 0.3s',
                                        opacity: autoMode.loading ? 0.6 : 1,
                                    }}
                                >
                                    <span style={{
                                        position: 'absolute', top: 3, left: autoMode.enabled ? 28 : 3,
                                        width: 24, height: 24, borderRadius: '50%', background: '#fff',
                                        transition: 'left 0.25s', boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    }}>
                                        {autoMode.loading ? <Loader size={12} color="#a855f7" style={{ animation: 'spin 1s linear infinite' }} /> : null}
                                    </span>
                                </button>
                            </div>

                            {/* Active Config Preview (Only show if enabled and outing data exists) */}
                            {autoMode.enabled && outingData.formLink && (
                                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '10px 12px', borderRadius: '8px', marginTop: '1rem', fontSize: '0.85rem' }}>
                                    <div style={{ color: '#818cf8', fontWeight: 'bold', marginBottom: '8px', fontSize: '0.75rem' }}>CURRENT ADMIN CONFIGURATION</div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                        <span style={{ color: '#94a3b8' }}>Reason:</span>
                                        <span style={{ color: '#e2e8f0', fontWeight: 'bold' }}>{outingData.reason || 'Not set'}</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span style={{ color: '#94a3b8' }}>Duration:</span>
                                        <span style={{ color: '#e2e8f0', fontWeight: 'bold' }}>{outingData.startDate} to {outingData.endDate}</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Generator Panel */}
                    <div className="dashboard-gen-card">
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '0.25rem' }}>
                            <Calendar size={18} color="#818cf8" />
                            <span style={{ fontWeight: 'bold', fontSize: '0.9rem', color: 'white' }}>Quick Submit</span>
                        </div>

                        {/* Form Link Input */}
                        <div className="dash-input-group">
                            <label className="dash-label">FORM LINK</label>
                            <input
                                type="url"
                                name="formLink"
                                value={outingData.formLink}
                                onChange={handleDateChange}
                                placeholder="https://forms.office.com/..."
                                className="dash-input"
                            />
                        </div>

                        {/* Reason Input */}
                        <div className="dash-input-group">
                            <label className="dash-label">REASON</label>
                            <input
                                type="text"
                                name="reason"
                                value={outingData.reason || ''}
                                onChange={handleDateChange}
                                placeholder="e.g. Home Visit, Medical Checkup..."
                                className="dash-input"
                            />
                        </div>

                        <div className="dash-form-row">
                            <div className="dash-form-col dash-input-group">
                                <label className="dash-label">START</label>
                                <input type="date" name="startDate" value={outingData.startDate} onChange={handleDateChange} className="dash-input" />
                            </div>
                            <div className="dash-form-col dash-input-group">
                                <label className="dash-label">END</label>
                                <input type="date" name="endDate" value={outingData.endDate} onChange={handleDateChange} className="dash-input" />
                            </div>
                        </div>

                        {/* One-Click Auto Submit for Paid Users */}
                        {autoMode.planType && autoMode.planType !== 'free' && (
                            <div style={{ marginBottom: '1rem' }}>
                                <button
                                    onClick={handleSubmitForm}
                                    disabled={submission.loading || !outingData.formLink}
                                    className="btn-dash"
                                    style={{
                                        width: '100%',
                                        background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        padding: '12px',
                                        borderRadius: '12px',
                                        border: 'none',
                                        cursor: (submission.loading || !outingData.formLink) ? 'not-allowed' : 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '8px',
                                        boxShadow: '0 4px 15px rgba(168, 85, 247, 0.4)',
                                        opacity: (submission.loading || !outingData.formLink) ? 0.7 : 1
                                    }}
                                >
                                    <Zap size={18} fill="white" />
                                    {submission.loading ? 'Processing...' : '⚡ Auto-Submit Now'}
                                </button>
                                <p style={{ fontSize: '0.7rem', color: '#94a3b8', textAlign: 'center', marginTop: '6px' }}>
                                    Uses institutional dates & reason automatically.
                                </p>
                            </div>
                        )}

                        {/* Buttons Row */}
                        <div className="dash-form-row pt-2">
                            <button onClick={handleGeneratePdf} className="btn-dash btn-dash-secondary dash-form-col">
                                <Download size={16} /> PDF
                            </button>
                            <button
                                onClick={handleSubmitForm}
                                disabled={submission.loading}
                                className="btn-dash dash-form-col"
                                style={{
                                    flex: 2,
                                    background: submission.loading ? 'rgba(99, 102, 241, 0.5)' :
                                        submission.status === 'completed' ? 'linear-gradient(135deg, #22c55e, #16a34a)' :
                                            submission.status === 'failed' ? 'linear-gradient(135deg, #ef4444, #dc2626)' :
                                                'linear-gradient(135deg, #6366f1, #4f46e5)',
                                    color: 'white',
                                    cursor: submission.loading ? 'wait' : 'pointer',
                                    boxShadow: submission.loading || submission.status !== null ? 'none' : '0 10px 20px rgba(99, 102, 241, 0.3)'
                                }}
                            >
                                {submission.loading ? (
                                    <><Loader size={18} className="spin" /> Submitting...</>
                                ) : submission.status === 'completed' ? (
                                    <><CheckCircle size={18} /> Done!</>
                                ) : submission.status === 'failed' ? (
                                    <><AlertCircle size={18} /> Retry</>
                                ) : (
                                    <><Send size={18} /> Submit Now</>
                                )}
                            </button>
                        </div>

                        {/* Status Message */}
                        {submission.message && (
                            <div style={{
                                fontSize: '0.8rem',
                                padding: '8px 12px',
                                borderRadius: '8px',
                                background: submission.status === 'completed' ? 'rgba(34, 197, 94, 0.2)' :
                                    submission.status === 'failed' ? 'rgba(239, 68, 68, 0.2)' :
                                        'rgba(99, 102, 241, 0.2)',
                                color: submission.status === 'completed' ? '#4ade80' :
                                    submission.status === 'failed' ? '#f87171' :
                                        '#a5b4fc'
                            }}>
                                {submission.loading && submission.progress > 0 && (
                                    <div style={{ marginBottom: '4px' }}>
                                        <div style={{
                                            width: '100%',
                                            height: '4px',
                                            background: 'rgba(0,0,0,0.3)',
                                            borderRadius: '2px',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{
                                                width: `${submission.progress}%`,
                                                height: '100%',
                                                background: '#6366f1',
                                                transition: 'width 0.3s ease'
                                            }} />
                                        </div>
                                    </div>
                                )}
                                {submission.message}
                            </div>
                        )}
                    </div>
                </div>

                <div className="dashboard-grid">
                    <div className="dashboard-card">
                        <div className="dash-card-header"><User size={20} className="dash-card-icon" /><span className="dash-card-title">Personal Info</span></div>
                        <DetailRow label="Phone" value={profile?.student_phone} />
                        <DetailRow label="Date of Birth" value={profile?.dob} />
                        <DetailRow label="Gender" value={profile?.gender} />
                    </div>

                    <div className="dashboard-card">
                        <div className="dash-card-header"><Users size={20} className="dash-card-icon" /><span className="dash-card-title">Parent Details</span></div>
                        <div style={{ marginBottom: '10px' }}>
                            <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: theme.textMuted, marginBottom: '5px' }}>FATHER</div>
                            <DetailRow label="Name" value={profile?.parent1_name} />
                            <DetailRow label="Phone" value={profile?.parent1_phone} />
                        </div>
                        <div>
                            <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: theme.textMuted, marginBottom: '5px' }}>MOTHER</div>
                            <DetailRow label="Name" value={profile?.parent2_name} />
                            <DetailRow label="Phone" value={profile?.parent2_phone} />
                        </div>
                    </div>

                    <div className="dashboard-card">
                        <div className="dash-card-header"><PenTool size={20} className="dash-card-icon" /><span className="dash-card-title">Signature</span></div>
                        {profile?.signature_data ? (
                            <div className="dash-signature-box">
                                <img
                                    src={(profile.signature_data?.startsWith('signatures/') || profile.signature_data?.startsWith('signatures\\')) ? `${getBaseUrl()}/${profile.signature_data.replace(/\\/g, '/')}` : profile.signature_data}
                                    alt="Sign"
                                    style={{ height: '40px' }}
                                />
                            </div>
                        ) : (
                            <div className="dash-signature-box" style={{ border: '2px dashed #ef4444', color: '#ef4444' }}>No Signature</div>
                        )}
                        <p style={{ fontSize: '0.8rem', color: theme.textMuted, marginTop: '10px' }}>
                            This signature will be auto-placed on your generated forms.
                        </p>
                    </div>
                </div>
            </main>

            {/* Credential Reverify Modal */}
            {reverifyModal.show && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(10px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000, padding: '1rem'
                }}>
                    <div style={{
                        background: theme.card, borderRadius: '20px', border: theme.cardBorder,
                        padding: '2rem', maxWidth: '450px', width: '100%',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)'
                    }}>
                        <div style={{ marginBottom: '1.5rem' }}>
                            <AlertCircle size={48} style={{ color: '#f59e0b', marginBottom: '1rem' }} />
                            <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem', color: 'white' }}>
                                Re-verify Your Credentials
                            </h3>
                            <p style={{ color: theme.textMuted, fontSize: '0.9rem' }}>
                                For security reasons, please re-enter your Outlook password to continue.
                                This will securely update your encrypted credentials.
                            </p>
                        </div>

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: 'white' }}>
                                Outlook Password
                            </label>
                            <input
                                type="password"
                                value={reverifyModal.password}
                                onChange={(e) => setReverifyModal(prev => ({ ...prev, password: e.target.value, error: '' }))}
                                onKeyPress={(e) => e.key === 'Enter' && handleReverifyCredentials()}
                                placeholder="Enter your Outlook password"
                                disabled={reverifyModal.loading}
                                style={{
                                    width: '100%', padding: '0.75rem 1rem', borderRadius: '12px',
                                    border: `1px solid ${reverifyModal.error ? '#ef4444' : 'rgba(255,255,255,0.1)'}`,
                                    background: 'rgba(15, 23, 42, 0.5)', color: theme.text,
                                    fontSize: '1rem', outline: 'none',
                                    transition: 'all 0.2s'
                                }}
                            />
                            {reverifyModal.error && (
                                <p style={{ color: '#ef4444', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                                    {reverifyModal.error}
                                </p>
                            )}
                        </div>

                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button
                                onClick={() => setReverifyModal({ show: false, loading: false, password: '', error: '' })}
                                disabled={reverifyModal.loading}
                                style={{
                                    flex: 1, padding: '0.75rem 1.5rem', borderRadius: '12px',
                                    border: '1px solid rgba(255,255,255,0.1)', background: 'transparent',
                                    color: theme.text, fontSize: '1rem', fontWeight: '600',
                                    cursor: reverifyModal.loading ? 'not-allowed' : 'pointer',
                                    opacity: reverifyModal.loading ? 0.5 : 1,
                                    transition: 'all 0.2s'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleReverifyCredentials}
                                disabled={reverifyModal.loading}
                                style={{
                                    flex: 1, padding: '0.75rem 1.5rem', borderRadius: '12px',
                                    border: 'none', background: theme.primary,
                                    color: 'white', fontSize: '1rem', fontWeight: '600',
                                    cursor: reverifyModal.loading ? 'not-allowed' : 'pointer',
                                    opacity: reverifyModal.loading ? 0.7 : 1,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    gap: '0.5rem', transition: 'all 0.2s'
                                }}
                            >
                                {reverifyModal.loading ? (
                                    <>
                                        <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} />
                                        Verifying...
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle size={16} />
                                        Verify
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}


        </div>
    );
};

export default Dashboard;
