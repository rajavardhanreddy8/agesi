import React from 'react';
import { EmailVerification } from '../components/auth/EmailVerification';
import Navigation from '../components/Navigation';

const VerifyEmail = () => (
    <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="py-12">
            <EmailVerification />
        </div>
    </div>
);

export default VerifyEmail;
