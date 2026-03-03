import React from 'react';
import { Link } from 'react-router-dom';
import Navigation from '../components/Navigation';
import Footer from '../components/Footer';
import { auth } from '../utils/auth';

const Landing = () => {
    const features = [
        { icon: '📄', title: 'Auto-Fill Forms', desc: 'Securely extract details from your documents automatically.', color: '#6366f1' },
        { icon: '💸', title: 'Just ₹50 / mo', desc: 'One simple, ultra-affordable payment.', color: '#10b981' },
        { icon: '🚀', title: 'One-Click Submit', desc: 'Generate PDF and submit to portal with a single click.', color: '#f97316' },
    ];

    return (
        <div style={{ minHeight: '100vh', background: '#0f172a', fontFamily: "'Inter', sans-serif" }}>
            <Navigation />
            <div className="landing-hero">
                <div className="landing-badge">Now Available ✨</div>
                <h1 className="landing-title">
                    Campus Outing<br />Made Simple
                </h1>
                <p className="landing-subtitle">
                    Automate your leave requests with AI-powered form filling.
                    No more tedious typing—just ₹50 per month.
                </p>
                <div className="landing-btn-container">
                    {auth.isAuthenticated() ? (
                        <Link to="/dashboard" className="landing-btn-primary">
                            📱 Go to Dashboard
                        </Link>
                    ) : (
                        <>
                            <Link to="/register" className="landing-btn-primary">
                                🚀 Get Started Now
                            </Link>
                            <Link to="/login" className="landing-btn-secondary">
                                Sign In
                            </Link>
                        </>
                    )}
                </div>

                <div className="landing-features">
                    {features.map((f, i) => (
                        <div key={i} className="landing-feature-card">
                            <div className="landing-feature-icon" style={{ background: `${f.color}20` }}>
                                {f.icon}
                            </div>
                            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.5rem', color: '#f8fafc' }}>
                                {f.title}
                            </h3>
                            <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                                {f.desc}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default Landing;
