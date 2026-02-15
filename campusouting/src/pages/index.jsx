import React from 'react';
import Navigation from '../components/Navigation';
import Footer from '../components/Footer';

const Landing = () => {
    const heroStyle = {
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '2rem',
        background: 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.15) 0%, transparent 60%)',
    };

    const titleStyle = {
        fontSize: 'clamp(2.5rem, 8vw, 4rem)',
        fontWeight: '800',
        marginBottom: '1.5rem',
        background: 'linear-gradient(135deg, #fff 0%, #6366f1 50%, #10b981 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        lineHeight: '1.1',
    };

    const subtitleStyle = {
        fontSize: '1.25rem',
        color: '#94a3b8',
        maxWidth: '600px',
        marginBottom: '2.5rem',
    };

    const buttonContainerStyle = {
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap',
        justifyContent: 'center',
    };

    const primaryBtnStyle = {
        background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
        color: 'white',
        padding: '1rem 2rem',
        borderRadius: '0.75rem',
        border: 'none',
        fontSize: '1rem',
        fontWeight: '600',
        cursor: 'pointer',
        textDecoration: 'none',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        transition: 'all 0.3s ease',
        boxShadow: '0 10px 40px rgba(99, 102, 241, 0.3)',
    };

    const secondaryBtnStyle = {
        background: 'transparent',
        color: '#f8fafc',
        padding: '1rem 2rem',
        borderRadius: '0.75rem',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        fontSize: '1rem',
        fontWeight: '600',
        cursor: 'pointer',
        textDecoration: 'none',
        transition: 'all 0.3s ease',
    };

    const featuresStyle = {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.5rem',
        maxWidth: '1000px',
        margin: '4rem auto 0',
        padding: '0 1rem',
    };

    const featureCardStyle = {
        background: 'rgba(30, 41, 59, 0.6)',
        backdropFilter: 'blur(10px)',
        borderRadius: '1rem',
        padding: '1.5rem',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        textAlign: 'left',
    };

    const featureIconStyle = {
        width: '48px',
        height: '48px',
        borderRadius: '0.75rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '1rem',
        fontSize: '1.5rem',
    };

    const features = [
        { icon: '📄', title: 'Auto-Fill Forms', desc: 'Upload your document and let AI extract all details automatically.', color: '#6366f1' },
        { icon: '🔐', title: 'Secure Login', desc: 'Your Outlook credentials are encrypted and stored safely.', color: '#10b981' },
        { icon: '🚀', title: 'One-Click Submit', desc: 'Generate PDF and submit to portal with a single click.', color: '#f97316' },
    ];

    return (
        <div style={{ minHeight: '100vh' }}>
            <Navigation />
            <div style={heroStyle}>
                <h1 style={titleStyle}>
                    Campus Outing<br />Made Simple
                </h1>
                <p style={subtitleStyle}>
                    Automate your leave requests with AI-powered form filling.
                    Upload your document, generate PDFs, and submit instantly.
                </p>
                <div style={buttonContainerStyle}>
                    <a href="/register" style={primaryBtnStyle}>
                        🚀 Get Started Free
                    </a>
                    <a href="/login" style={secondaryBtnStyle}>
                        Sign In
                    </a>
                </div>

                <div style={featuresStyle}>
                    {features.map((f, i) => (
                        <div key={i} style={featureCardStyle}>
                            <div style={{ ...featureIconStyle, background: `${f.color}20` }}>
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
