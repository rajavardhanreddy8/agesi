import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auth } from '../utils/auth';

const Navigation = () => {
    const user = auth.getUser();

    const handleLogout = () => {
        auth.logout();
    };

    const navStyle = {
        position: 'sticky',
        top: 0,
        zIndex: 50,
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    };

    const containerStyle = {
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '0 1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        height: '64px',
    };

    const logoStyle = {
        fontSize: '1.25rem',
        fontWeight: '700',
        background: 'linear-gradient(135deg, #6366f1, #10b981)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        textDecoration: 'none',
    };

    const linkStyle = {
        color: '#94a3b8',
        textDecoration: 'none',
        padding: '0.5rem 1rem',
        borderRadius: '0.5rem',
        fontSize: '0.875rem',
        fontWeight: '500',
        transition: 'all 0.3s ease',
    };

    const buttonStyle = {
        background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
        color: 'white',
        padding: '0.5rem 1rem',
        borderRadius: '0.5rem',
        border: 'none',
        fontSize: '0.875rem',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
    };

    const userNameStyle = {
        color: '#94a3b8',
        fontSize: '0.875rem',
        padding: '0.5rem',
    };

    return (
        <nav style={navStyle}>
            <div style={containerStyle}>
                <Link to="/" style={logoStyle}>
                    🚀 Outing Automation
                </Link>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {auth.isAuthenticated() ? (
                        <>
                            <Link to="/dashboard" style={linkStyle}>Dashboard</Link>
                            <Link to="/profile" style={linkStyle}>Profile</Link>
                            <Link to="/plans" style={{ ...linkStyle, background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: 'white', borderRadius: '0.5rem' }}>💎 Plans</Link>
                            <span style={userNameStyle}>Hi, {user?.full_name?.split(' ')[0] || 'User'}</span>
                            <button onClick={handleLogout} style={buttonStyle}>
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" style={linkStyle}>Login</Link>
                            <Link to="/register" style={buttonStyle}>Get Started</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navigation;
