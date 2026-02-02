import React from 'react';
import Navigation from '../../components/Navigation';
import Footer from '../../components/Footer';

const ContactUs = () => {
    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Navigation />
            <div style={{ flex: 1, maxWIdth: '800px', margin: '4rem auto', padding: '0 1.5rem', color: '#f8fafc' }}>
                <h1 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '2rem' }}>Contact Us</h1>
                <p>Have questions or need support? We're here to help!</p>

                <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '1rem', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>Support Email</h2>
                    <p style={{ fontSize: '1.1rem', color: '#6366f1' }}>campusouting.go@gmail.com</p>
                </div>

                <div style={{ marginTop: '2rem' }}>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>Operating Hours</h2>
                    <p>Monday - Friday: 9:00 AM - 6:00 PM IST</p>
                    <p>Response time: Within 24 hours</p>
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default ContactUs;
