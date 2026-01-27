import React, { useState, useEffect } from 'react';
import { auth } from '../../utils/auth';

export const EmailVerification = () => {
    const [isVerifying, setIsVerifying] = useState(true);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const verifyEmail = async () => {
            // Get token from URL
            const params = new URLSearchParams(window.location.search);
            const token = params.get('token');

            if (!token) {
                setError('Invalid verification link');
                setIsVerifying(false);
                return;
            }

            try {
                const result = await auth.verifyEmail(token);

                if (result.success) {
                    setSuccess(true);
                    // Redirect to login after 3 seconds
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 3000);
                }

            } catch (err) {
                setError(err.response?.data?.error || 'Verification failed');
            } finally {
                setIsVerifying(false);
            }
        };

        verifyEmail();
    }, []);

    return (
        <div className="verification-container" style={{ textAlign: 'center', padding: '50px' }}>
            {isVerifying && (
                <div>
                    <h2>Verifying your email...</h2>
                    <div className="spinner">Waiting...</div>
                </div>
            )}

            {success && (
                <div className="alert alert-success" style={{ color: 'green' }}>
                    <h2>✅ Email Verified!</h2>
                    <p>Your email has been verified successfully.</p>
                    <p>Redirecting to login...</p>
                </div>
            )}

            {error && (
                <div className="alert alert-error" style={{ color: 'red' }}>
                    <h2>❌ Verification Failed</h2>
                    <p>{error}</p>
                    <a href="/register" className="btn btn-primary">
                        Register Again
                    </a>
                </div>
            )}
        </div>
    );
};
