import React from 'react';
import Navigation from '../../components/Navigation';
import Footer from '../../components/Footer';

const PrivacyPolicy = () => {
    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Navigation />
            <div style={{ flex: 1, maxWIdth: '800px', margin: '4rem auto', padding: '0 1.5rem', color: '#f8fafc' }}>
                <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '2rem' }}>Privacy Policy</h1>
                <p>Last updated: February 02, 2026</p>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>1. Introduction</h2>
                    <p>Welcome to Campus Outing. We respect your privacy and are committed to protecting your personal data.</p>
                </section>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>2. Data We Collect</h2>
                    <p>We collect information you provide directly to us, such as when you create an account, including your email, roll number, and encrypted Outlook credentials (used only for automated submissions).</p>
                </section>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>3. How We Use Data</h2>
                    <p>Your data is used solely to provide the automated outing submission service. We do not sell or share your data with third parties.</p>
                </section>
            </div>
            <Footer />
        </div>
    );
};

export default PrivacyPolicy;
