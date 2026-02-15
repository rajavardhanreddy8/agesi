import React from 'react';
import Navigation from '../../components/Navigation';
import Footer from '../../components/Footer';

const TermsConditions = () => {
    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Navigation />
            <div style={{ flex: 1, maxWIdth: '800px', margin: '4rem auto', padding: '0 1.5rem', color: '#f8fafc' }}>
                <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '2rem' }}>Terms & Conditions</h1>
                <p>Last updated: February 02, 2026</p>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>1. Acceptance of Terms</h2>
                    <p>By using Outing Automation, you agree to these terms. If you do not agree, please do not use the service.</p>
                </section>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>2. Service Description</h2>
                    <p>Outing Automation provides AI-assisted form filling and automated submission to campus portals. Accuracy depends on the data provided by the user.</p>
                </section>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>3. User Responsibility</h2>
                    <p>Users are responsible for the accuracy of their submissions and maintaining the confidentiality of their account credentials.</p>
                </section>
            </div>
            <Footer />
        </div>
    );
};

export default TermsConditions;
