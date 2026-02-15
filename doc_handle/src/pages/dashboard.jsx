
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, BookOpen, Users, PenTool, Download, LogOut, Calendar, Edit3, Send, Loader, CheckCircle, AlertCircle } from 'lucide-react';
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
                        if (!plan || (plan.plan_type !== 'basic' && plan.plan_type !== 'premium')) {
                            // No valid plan, redirect to payment
                            console.log("No active plan found, redirecting to plans...");
                            navigate('/plans');
                            return;
                        }
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
                    reason: ''
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
        if (!profile?.student_email) missingFields.push('Student Email');
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
                setSubmission(prev => ({
                    ...prev,
                    taskId: res.data.task_id,
                    status: 'pending',
                    message: 'Task queued...',
                    queuePosition: res.data.queue_position
                }));

                // Poll for status
                let retryCount = 0;
                let errorCount = 0;
                const maxRetries = 600; // 10-20 minutes depending on speed

                const pollStatus = async () => {
                    if (retryCount >= maxRetries) {
                        setSubmission(prev => ({
                            ...prev,
                            loading: false,
                            status: 'failed',
                            message: '❌ Submission is taking longer than usual. Please check the History tab in a few minutes to see if it completed.'
                        }));
                        return;
                    }
                    retryCount++;

                    try {
                        const statusRes = await api.get(`/task-status/${res.data.task_id}`);
                        const task = statusRes.data.task || statusRes.data; // Handle both formats if needed

                        setSubmission(prev => ({
                            ...prev,
                            status: task.status,
                            message: task.message || task.status,
                            progress: task.progress || 0,
                            queuePosition: task.queue_position !== undefined ? task.queue_position : prev.queuePosition
                        }));

                        if (task.status === 'completed') {
                            setSubmission(prev => ({ ...prev, loading: false, message: '✅ Form submitted successfully!' }));
                        } else if (task.status === 'failed') {
                            setSubmission(prev => ({ ...prev, loading: false, message: `❌ Failed: ${task.error || 'Unknown error'}` }));

                            // Check for auth failure in error message or status
                            if (task.error && (
                                task.error.includes('Invalid credentials') ||
                                task.error.includes('Login failed') ||
                                task.error.includes('Authentication failed')
                            )) {
                                setReverifyModal({ show: true, loading: false, password: '', error: 'Previous login failed. Please re-verify your password.' });
                            }
                        } else {
                            // Continue polling
                            setTimeout(pollStatus, 2000);
                        }
                    } catch (e) {
                        console.error('Status poll error:', e);
                        errorCount++;
                        if (errorCount > 5) {
                            setSubmission(prev => ({ ...prev, loading: false, status: 'failed', message: '❌ Connection lost. Please check history.' }));
                        } else {
                            setTimeout(pollStatus, 3000);
                        }
                    }
                };

                pollStatus();
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

    // Inline Styles System
    const theme = {
        bg: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        card: 'rgba(30, 41, 59, 0.7)',
        cardBorder: '1px solid rgba(255,255,255,0.08)',
        text: '#f8fafc',
        textMuted: '#94a3b8',
        primary: 'linear-gradient(135deg, #6366f1, #4f46e5)',
        accent: 'linear-gradient(135deg, #a855f7, #9333ea)',
    };

    const s = {
        container: { minHeight: '100vh', background: theme.bg, color: theme.text, fontFamily: 'sans-serif' },
        header: {
            padding: '1rem 2rem', background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(10px)',
            borderBottom: theme.cardBorder, position: 'sticky', top: 0, zIndex: 50,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        },
        logo: { fontSize: '1.5rem', fontWeight: 'bold', background: theme.primary, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
        main: { maxWidth: '1200px', margin: '0 auto', padding: '2rem' },

        // Hero Section
        hero: {
            background: theme.card, borderRadius: '24px', border: theme.cardBorder, padding: '2.5rem',
            marginBottom: '2rem', display: 'flex', flexDirection: 'row', gap: '2rem', flexWrap: 'wrap',
            alignItems: 'center', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        },
        avatar: {
            width: '100px', height: '100px', borderRadius: '20px', background: theme.primary,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.5rem', fontWeight: 'bold', color: 'white'
        },
        heroContent: { flex: 1 },
        heroTitle: { fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '0.5rem', color: 'white' },
        badges: { display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' },
        badge: { background: 'rgba(0,0,0,0.3)', padding: '4px 12px', borderRadius: '12px', fontSize: '0.85rem', color: theme.textMuted, border: theme.cardBorder },

        btnGroup: { display: 'flex', gap: '1rem', flexWrap: 'wrap' },
        btnPrimary: {
            background: theme.primary, color: 'white', border: 'none', padding: '12px 24px', borderRadius: '12px',
            fontSize: '1rem', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px',
            boxShadow: '0 10px 20px rgba(99, 102, 241, 0.3)'
        },
        btnSecondary: {
            background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '12px',
            fontSize: '1rem', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px'
        },

        // Generator Card
        genCard: {
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9))',
            borderRadius: '24px', padding: '1.5rem', border: '1px solid rgba(99, 102, 241, 0.3)',
            display: 'flex', flexDirection: 'column', gap: '1rem', minWidth: '300px'
        },
        input: {
            width: '100%', padding: '10px', borderRadius: '8px', border: theme.cardBorder,
            background: 'rgba(0,0,0,0.3)', color: 'white', fontSize: '0.9rem', outline: 'none'
        },

        // Grid
        grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' },
        card: { background: theme.card, borderRadius: '16px', border: theme.cardBorder, padding: '1.5rem' },
        cardHeader: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' },
        cardIcon: { background: 'rgba(99, 102, 241, 0.1)', padding: '8px', borderRadius: '8px', color: '#818cf8' },
        cardTitle: { fontWeight: 'bold', fontSize: '1.1rem' },
        row: { display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.9rem' },
        rowLabel: { color: theme.textMuted },

        signatureBox: {
            background: 'white', padding: '10px', borderRadius: '8px', marginTop: '10px',
            border: '2px dashed #cbd5e1', display: 'inline-block'
        }
    };

    if (loading) return <div style={{ ...s.container, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>;

    const DetailRow = ({ label, value }) => (
        <div style={s.row}>
            <span style={s.rowLabel}>{label}</span>
            <span style={{ fontWeight: 500 }}>{value || 'N/A'}</span>
        </div>
    );

    return (
        <div style={s.container}>
            <header style={s.header}>
                <div style={s.logo}>Outing Agent</div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span style={{ color: theme.textMuted, fontSize: '0.9rem' }}>Welcome, {profile?.full_name?.split(' ')[0]}</span>
                    <button onClick={() => { auth.logout(); navigate('/login'); }} style={{ background: 'none', border: 'none', color: theme.textMuted, cursor: 'pointer' }}>
                        <LogOut size={20} />
                    </button>
                </div>
            </header>

            <main style={s.main}>
                <div style={s.hero}>
                    <div style={s.avatar}>{profile?.full_name?.charAt(0)}</div>
                    <div style={s.heroContent}>
                        <h1 style={s.heroTitle}>{profile?.full_name}</h1>
                        <div style={s.badges}>
                            <span style={s.badge}>{profile?.roll_number}</span>
                            <span style={s.badge}>{profile?.programme}</span>
                            <span style={s.badge}>{profile?.email}</span>
                        </div>
                        <div style={s.btnGroup}>
                            <button onClick={() => navigate('/profile')} style={s.btnSecondary}><Edit3 size={18} /> Edit Profile</button>
                            {profile?.is_admin && (
                                <button onClick={() => window.location.href = '/admin/dashboard'} style={{ ...s.btnSecondary, background: 'rgba(239, 68, 68, 0.2)', color: '#f87171' }}>🛡️ Admin Portal</button>
                            )}
                            <button onClick={() => navigate('/plans')} style={{ ...s.btnSecondary, background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24' }}>Upgrage Plan</button>
                        </div>
                    </div>

                    {/* Generator Panel */}
                    <div style={s.genCard}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Calendar size={18} color="#818cf8" />
                            <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Quick Submit</span>
                        </div>

                        {/* Form Link Input */}
                        <div>
                            <label style={{ fontSize: '0.75rem', color: theme.textMuted, display: 'block', marginBottom: '4px' }}>FORM LINK</label>
                            <input
                                type="url"
                                name="formLink"
                                value={outingData.formLink}
                                onChange={handleDateChange}
                                placeholder="https://forms.office.com/..."
                                style={s.input}
                            />
                        </div>

                        {/* Reason Input */}
                        <div>
                            <label style={{ fontSize: '0.75rem', color: theme.textMuted, display: 'block', marginBottom: '4px' }}>REASON</label>
                            <input
                                type="text"
                                name="reason"
                                value={outingData.reason || ''}
                                onChange={handleDateChange}
                                placeholder="e.g. Home Visit, Medical Checkup..."
                                style={s.input}
                            />
                        </div>

                        <div style={{ display: 'flex', gap: '10px' }}>
                            <div style={{ flex: 1 }}>
                                <label style={{ fontSize: '0.75rem', color: theme.textMuted, display: 'block', marginBottom: '4px' }}>START</label>
                                <input type="date" name="startDate" value={outingData.startDate} onChange={handleDateChange} style={s.input} />
                            </div>
                            <div style={{ flex: 1 }}>
                                <label style={{ fontSize: '0.75rem', color: theme.textMuted, display: 'block', marginBottom: '4px' }}>END</label>
                                <input type="date" name="endDate" value={outingData.endDate} onChange={handleDateChange} style={s.input} />
                            </div>
                        </div>

                        {/* Buttons Row */}
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <button onClick={handleGeneratePdf} style={{ ...s.btnSecondary, flex: 1 }}>
                                <Download size={16} /> PDF
                            </button>
                            <button
                                onClick={handleSubmitForm}
                                disabled={submission.loading}
                                style={{
                                    ...s.btnPrimary,
                                    flex: 2,
                                    background: submission.loading ? 'rgba(99, 102, 241, 0.5)' :
                                        submission.status === 'completed' ? 'linear-gradient(135deg, #22c55e, #16a34a)' :
                                            submission.status === 'failed' ? 'linear-gradient(135deg, #ef4444, #dc2626)' :
                                                'linear-gradient(135deg, #6366f1, #4f46e5)',
                                    cursor: submission.loading ? 'wait' : 'pointer'
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

                                {/* Live View Iframe */}
                                {(submission.status === 'running' || submission.status === 'pending') && submission.taskId && (
                                    <div style={{ marginTop: '15px' }}>
                                        <div style={{ fontSize: '0.7rem', color: theme.textMuted, marginBottom: '5px' }}>LIVE AUTOMATION MONITOR:</div>
                                        <iframe
                                            src={`https://outing-backend-api.azurewebsites.net/api/live-view/${submission.taskId}`}
                                            style={{
                                                width: '100%',
                                                height: '250px',
                                                border: '1px solid #334155',
                                                borderRadius: '8px',
                                                background: '#000'
                                            }}
                                            title="Live View"
                                        />
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                <div style={s.grid}>
                    <div style={s.card}>
                        <div style={s.cardHeader}><User size={20} style={s.cardIcon} /><span style={s.cardTitle}>Personal Info</span></div>
                        <DetailRow label="Phone" value={profile?.student_phone} />
                        <DetailRow label="Date of Birth" value={profile?.dob} />
                        <DetailRow label="Gender" value={profile?.gender} />
                    </div>

                    <div style={s.card}>
                        <div style={s.cardHeader}><Users size={20} style={s.cardIcon} /><span style={s.cardTitle}>Parent Details</span></div>
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

                    <div style={s.card}>
                        <div style={s.cardHeader}><PenTool size={20} style={s.cardIcon} /><span style={s.cardTitle}>Signature</span></div>
                        {profile?.signature_data ? (
                            <div style={s.signatureBox}>
                                <img
                                    src={(profile.signature_data?.startsWith('signatures/') || profile.signature_data?.startsWith('signatures\\')) ? `${getBaseUrl()}/${profile.signature_data.replace(/\\/g, '/')}` : profile.signature_data}
                                    alt="Sign"
                                    style={{ height: '40px' }}
                                />
                            </div>
                        ) : (
                            <div style={{ ...s.signatureBox, border: '2px dashed #ef4444', color: '#ef4444' }}>No Signature</div>
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
                            <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                                Re-verify Your Credentials
                            </h3>
                            <p style={{ color: theme.textMuted, fontSize: '0.9rem' }}>
                                For security reasons, please re-enter your Outlook password to continue.
                                This will securely update your encrypted credentials.
                            </p>
                        </div>

                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
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
