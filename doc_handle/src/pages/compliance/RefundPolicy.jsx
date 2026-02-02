import React from 'react';
import Navigation from '../../components/Navigation';
import Footer from '../../components/Footer';

const RefundPolicy = () => {
    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Navigation />
            <div style={{ flex: 1, maxWIdth: '800px', margin: '4rem auto', padding: '0 1.5rem', color: '#f8fafc' }}>
                <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '2rem' }}>Cancellation & Refund Policy</h1>
                <p>Last updated: February 02, 2026</p>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>1. Subscriptions</h2>
                    <p>Subscription plans are billed in advance. We offer a 24-hour refund window for any technical failures during the first upgrade.</p>
                </section>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>2. Cancellations</h2>
                    <p>Users can cancel their automation services at any time from their dashboard. No prorated refunds are provided for partial months.</p>
                </section>
                <section style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1rem' }}>3. Processing</h2>
                    <p>Approved refunds will be processed via the original payment method within 5-7 business days.</p>
                </section>
            </div>
            <Footer />
        </div>
    );
};

export default RefundPolicy;
