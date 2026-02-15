import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
    const footerStyle = {
        background: '#0f172a',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        padding: '3rem 1.5rem',
        color: '#94a3b8',
        fontSize: '0.875rem',
    };

    const containerStyle = {
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '2rem',
    };

    const sectionTitleStyle = {
        color: '#f8fafc',
        fontWeight: '700',
        marginBottom: '1rem',
        fontSize: '1rem',
    };

    const listStyle = {
        listStyle: 'none',
        padding: 0,
        margin: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
    };

    const linkStyle = {
        color: '#94a3b8',
        textDecoration: 'none',
        transition: 'color 0.2s ease',
    };

    return (
        <footer style={footerStyle}>
            <div style={containerStyle}>
                <div>
                    <h3 style={sectionTitleStyle}>🚀 Outing Automation</h3>
                    <p>Automating leave requests for campus students since 2024.</p>
                </div>
                <div>
                    <h3 style={sectionTitleStyle}>Legal</h3>
                    <ul style={listStyle}>
                        <li><Link to="/privacy" style={linkStyle}>Privacy Policy</Link></li>
                        <li><Link to="/terms" style={linkStyle}>Terms & Conditions</Link></li>
                        <li><Link to="/refund-policy" style={linkStyle}>Cancellation/Refund Policy</Link></li>
                    </ul>
                </div>
                <div>
                    <h3 style={sectionTitleStyle}>Support</h3>
                    <ul style={listStyle}>
                        <li><Link to="/contact" style={linkStyle}>Contact Us</Link></li>
                        <li><Link to="/plans" style={linkStyle}>Pricing</Link></li>
                    </ul>
                </div>
            </div>
            <div style={{ textAlign: 'center', marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <p>&copy; {new Date().getFullYear()} Outing Automation. All rights reserved.</p>
            </div>
        </footer>
    );
};

export default Footer;
